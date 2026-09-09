# 用户权限管理说明

## 权限级别

### 👑 管理员 (admin)
**拥有所有权限**
- ✅ 查看所有用户
- ✅ 创建新用户
- ✅ 编辑用户信息
- ✅ 删除用户（除管理员外）
- ✅ 启用/禁用用户账户
- ✅ 修改用户角色

### 👤 普通用户 (user)
**只读权限**
- ✅ 查看其他普通用户列表
- ❌ 不能创建用户
- ❌ 不能编辑用户
- ❌ 不能删除用户
- ❌ 不能修改用户角色

## 权限控制实现

### 前端权限控制

```javascript
// 权限检查函数
function hasPermission(action) {
  const userRole = currentUser.value.role;
  
  switch (action) {
    case 'create_user':
    case 'edit_user':
    case 'delete_user':
      return userRole === 'admin';
    case 'view_users':
      return ['admin', 'user'].includes(userRole);
    default:
      return false;
  }
}
```

### 后端权限控制

```python
# 用户视图集权限控制
class UserViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ADMIN:
            return User.objects.all()  # 管理员看所有用户
        elif user.role == User.Role.USER:
            return User.objects.filter(role=User.Role.USER)  # 普通用户看其他普通用户
        else:
            return User.objects.none()  # 其他情况无权限
    
    def perform_create(self, serializer):
        if self.request.user.role != User.Role.ADMIN:
            raise PermissionError("只有管理员可以创建用户")
    
    def perform_destroy(self, instance):
        if self.request.user.role != User.Role.ADMIN:
            raise PermissionError("只有管理员可以删除用户")
        if instance.role == User.Role.ADMIN:
            raise PermissionError("不能删除管理员账户")
```

## 安全保护

### 🔒 管理员账户保护
- 管理员账户不能被删除
- 删除按钮对管理员账户自动禁用
- 后端也会检查并阻止删除管理员

### 🛡️ 权限验证
- 前端：基于用户角色的UI控制
- 后端：API级别的权限验证
- 双重保护确保安全性

## 使用场景

### 管理员操作
1. 登录系统（admin/admin123456）
2. 进入"系统管理" → "用户管理"
3. 可以执行所有用户管理操作

### 普通用户查看
1. 登录系统（user1/user123）
2. 进入"系统管理" → "用户管理"
3. 只能查看其他普通用户列表，无操作权限

## 权限升级

如需修改权限配置，可以：

1. **修改前端权限检查函数**
2. **调整后端权限控制逻辑**
3. **更新用户角色定义**

## 注意事项

- 权限控制在前端和后端都有实现
- 后端权限控制是最终的安全保障
- 管理员账户具有最高权限，请谨慎使用
- 建议定期审查用户权限设置
