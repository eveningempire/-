# Flask "Restarting with stat" 行为解释

## 现象

在启动Flask应用时，你可能会看到以下输出：

```
* Serving Flask app 'app'
* Debug mode: on
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:8005
* Running on http://10.35.8.214:8005
* Restarting with stat
```

然后再次显示：

```
[INFO] Try to connect database on 'sqlite:///.\static\database\ate_phm_db_2024.db'
[INFO] Seemingly succeed to connecting database on 'sqlite:///.\static\database\ate_phm_db_2024.db'
```

## 解释

这是正常的行为，不是错误。这种重启是由Flask的开发服务器有意设计的，特别是当你在调试模式（`Debug mode: on`）下运行应用时：

1. **自动重载机制**：`Restarting with stat` 意味着Flask正在使用其自动重载机制，它会监视你的代码文件变化。当检测到文件变化时，Flask会自动重新启动服务器以应用这些更改。

2. **两个进程**：Flask实际上启动了两个进程 - 一个是主进程，用于监视文件变化；另一个是子进程，用于实际运行你的Flask应用。当你首次启动应用时，它会启动这两个进程，这就是为什么你会看到两次数据库连接消息。

3. **初始化阶段**：即使没有文件变化，在初始启动时Flask也会执行这个"重启"，因为它需要启动子进程来运行应用。这是开发模式的正常行为。

## 何时应该担心

这种行为只有在以下情况下才应该引起关注：

1. 如果应用在没有文件变化的情况下持续不断地重启（每几秒一次）
2. 如果重启后应用无法正常工作或抛出错误
3. 如果第二次启动时无法建立之前成功的连接（如数据库连接）

## 如何禁用这种行为

如果你在生产环境中，应该禁用调试模式。在Flask中，这通常意味着设置：

```python
app.debug = False
```

或者在使用`flask run`命令时不添加`--debug`标志。

但对于开发环境，这种自动重启功能非常有用，因为它允许你更改代码而无需手动重启服务器。

## 结论

"Restarting with stat"是Flask开发服务器在调试模式下的正常行为，不是错误情况。只要你的应用能正常运行，可以安全地忽略这条消息。
