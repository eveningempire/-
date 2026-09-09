/**
 * WebSocket服务 - 实时数据连接管理
 * 提供WebSocket连接管理、自动重连、消息处理等功能
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.url = '';
    this.isConnecting = false;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000; // 3秒
    this.messageHandlers = new Map();
    this.onConnectCallbacks = [];
    this.onDisconnectCallbacks = [];
    this.onErrorCallbacks = [];
    this.heartbeatInterval = null;
    this.heartbeatTimer = 30000; // 30秒心跳
    this.lastPingTime = null;

    // 多候选主机，用于开发环境端口回退（5173 -> 8001 -> 8000）
    this.hostCandidates = [];
    this.hostIndex = 0;
  }

  /**
   * 连接WebSocket
   * @param {string} cmgId - CMG ID，可选
   * @returns {Promise<void>}
   */
  async connect(cmgId = null) {
    if (this.isConnecting || this.isConnected) {
      return;
    }

    this.isConnecting = true;

    // 根据当前环境构建候选主机列表
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const hostname = window.location.hostname;
    const port = window.location.port;
    if (port === '5173') {
      // Vite 开发端口，优先直连后端 ASGI/Daphne(8001)，次选 8000
      this.hostCandidates = [
        `${hostname}:8001`,
        `${hostname}:8000`,
      ];
    } else {
      // 生产或直接访问后端
      this.hostCandidates = [window.location.host];
    }
    // 使用当前候选项
    const host = this.hostCandidates[this.hostIndex] || window.location.host;

    if (cmgId) {
      this.url = `${protocol}//${host}/ws/realtime/${cmgId}/`;
    } else {
      this.url = `${protocol}//${host}/ws/realtime/`;
    }

    try {
      this.ws = new WebSocket(this.url);
      this.setupEventHandlers();
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.isConnecting = false;
      this.handleError(error);
    }
  }

  /**
   * 设置WebSocket事件处理器
   */
  setupEventHandlers() {
    this.ws.onopen = (event) => {
      console.log('WebSocket connected:', this.url);
      this.isConnected = true;
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      
      // 启动心跳
      this.startHeartbeat();
      
      // 触发连接回调
      this.onConnectCallbacks.forEach(callback => {
        try {
          callback(event);
        } catch (error) {
          console.error('Connect callback error:', error);
        }
      });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Message parse error:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.isConnected = false;
      this.isConnecting = false;
      
      // 停止心跳
      this.stopHeartbeat();
      
      // 触发断开连接回调
      this.onDisconnectCallbacks.forEach(callback => {
        try {
          callback(event);
        } catch (error) {
          console.error('Disconnect callback error:', error);
        }
      });

      // 自动重连（非正常关闭），优先尝试切换候选主机
      if (event.code !== 1000) {
        if (this.hostIndex + 1 < this.hostCandidates.length) {
          this.hostIndex += 1;
          console.log(`Switching WS backend to ${this.hostCandidates[this.hostIndex]}`);
          this.connect(cmgId);
          return;
        }
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            this.connect(cmgId);
          }, this.reconnectInterval);
        }
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.handleError(error);
    };
  }

  /**
   * 处理接收到的消息
   * @param {Object} data - 消息数据
   */
  handleMessage(data) {
    const { type } = data;
    
    // 处理心跳响应
    if (type === 'pong') {
      this.lastPingTime = Date.now();
      return;
    }

    // 调用注册的消息处理器
    const handlers = this.messageHandlers.get(type) || [];
    handlers.forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error(`Message handler error for type ${type}:`, error);
      }
    });

    // 调用通用消息处理器
    const allHandlers = this.messageHandlers.get('*') || [];
    allHandlers.forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error('Universal message handler error:', error);
      }
    });
  }

  /**
   * 处理错误
   * @param {Error} error - 错误对象
   */
  handleError(error) {
    this.onErrorCallbacks.forEach(callback => {
      try {
        callback(error);
      } catch (err) {
        console.error('Error callback error:', err);
      }
    });
  }

  /**
   * 发送消息
   * @param {Object} data - 要发送的数据
   * @returns {boolean} - 是否发送成功
   */
  send(data) {
    if (!this.isConnected || !this.ws) {
      console.warn('WebSocket not connected, cannot send message:', data);
      return false;
    }

    try {
      this.ws.send(JSON.stringify(data));
      return true;
    } catch (error) {
      console.error('Send message error:', error);
      return false;
    }
  }

  /**
   * 开始实时数据流
   * @param {number} interval - 数据推送间隔（秒）
   */
  startStream(interval = 1.0) {
    return this.send({
      command: 'start_stream',
      interval: interval
    });
  }

  /**
   * 停止实时数据流
   */
  stopStream() {
    return this.send({
      command: 'stop_stream'
    });
  }

  /**
   * 获取最新数据
   * @param {number} limit - 数据条数限制
   * @param {number} sinceMs - 起始时间戳（毫秒）
   */
  getLatest(limit = 100, sinceMs = null) {
    return this.send({
      command: 'get_latest',
      limit: limit,
      since_ms: sinceMs
    });
  }

  /**
   * 启动心跳
   */
  startHeartbeat() {
    this.stopHeartbeat(); // 确保只有一个心跳定时器
    
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({ command: 'ping' });
        
        // 检查心跳响应超时
        if (this.lastPingTime && (Date.now() - this.lastPingTime) > this.heartbeatTimer * 2) {
          console.warn('Heartbeat timeout, reconnecting...');
          this.disconnect();
          this.connect();
        }
      }
    }, this.heartbeatTimer);
  }

  /**
   * 停止心跳
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * 注册消息处理器
   * @param {string} type - 消息类型，使用 '*' 监听所有消息
   * @param {Function} handler - 处理函数
   */
  onMessage(type, handler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type).push(handler);
  }

  /**
   * 移除消息处理器
   * @param {string} type - 消息类型
   * @param {Function} handler - 处理函数
   */
  offMessage(type, handler) {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * 注册连接事件回调
   * @param {Function} callback - 回调函数
   */
  onConnect(callback) {
    this.onConnectCallbacks.push(callback);
  }

  /**
   * 注册断开连接事件回调
   * @param {Function} callback - 回调函数
   */
  onDisconnect(callback) {
    this.onDisconnectCallbacks.push(callback);
  }

  /**
   * 注册错误事件回调
   * @param {Function} callback - 回调函数
   */
  onError(callback) {
    this.onErrorCallbacks.push(callback);
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
  }

  /**
   * 获取连接状态
   */
  getStatus() {
    return {
      connected: this.isConnected,
      connecting: this.isConnecting,
      url: this.url,
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

// 创建全局WebSocket服务实例
const websocketService = new WebSocketService();

export default websocketService;
