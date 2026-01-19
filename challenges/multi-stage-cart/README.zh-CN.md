# 问题 2：电商购物车（多阶段）

本挑战测试你在管理技术债务和做出良好架构决策的同时，逐步构建复杂功能的能力。

## 概述

你将分**三个阶段**构建购物车服务。每个阶段都会增加复杂性，可能需要重构之前的代码。

**评分规则：**
- 必须通过第一阶段才能获得任何分数
- 完成第二阶段才能获得 B 或更高分数
- 第三阶段的质量决定 A 还是 B

---

## 第一阶段：基础购物车（入门级）

### 需求

为购物车服务构建 REST API：

| 接口 | 描述 |
|------|------|
| `POST /carts` | 为用户创建新购物车 |
| `GET /carts/:cartId` | 获取购物车内容 |
| `POST /carts/:cartId/items` | 添加商品到购物车 |
| `PATCH /carts/:cartId/items/:productId` | 更新商品数量 |
| `DELETE /carts/:cartId/items/:productId` | 从购物车移除商品 |
| `DELETE /carts/:cartId` | 清空/删除购物车 |

### 数据模型

```typescript
interface CartItem {
  productId: string;
  name: string;
  price: number;      // 价格（单位：分）
  quantity: number;
}

interface Cart {
  id: string;
  userId: string;
  items: CartItem[];
  createdAt: Date;
  updatedAt: Date;
}
```

### 交付物
- [ ] 所有接口可正常工作
- [ ] 基本输入验证
- [ ] 测试通过：`npm test -- --grep "Stage 1"`

---

## 第二阶段：库存与定价（中级）

**请在完成第一阶段后再阅读本节**

### 新增需求

#### 2.1 库存集成

现在提供了库存服务（见 `src/mocks/inventory.service.ts`）。

- 添加到购物车前，检查可用库存
- 处理：用户请求的数量 > 可用库存
- 处理：购物车中的商品变得不可用（库存降为 0）
- 接口：`POST /carts/:cartId/validate` - 检查所有商品是否仍然可用

#### 2.2 优惠码

支持以下类型的优惠码：
- `percentage` - 全场 X% 折扣
- `fixed_amount` - 全场减 X 元
- `buy_x_get_y` - 买 X 件送 Y 件（最便宜的商品免费）

优惠规则：
- 优惠码可以有最低购物金额要求
- 优惠码可以有过期日期
- 每个购物车只能使用一个优惠码

| 接口 | 描述 |
|------|------|
| `POST /carts/:cartId/discount` | 应用优惠码 |
| `DELETE /carts/:cartId/discount` | 移除优惠码 |

购物车响应现在应该包含：
```typescript
interface Cart {
  // ... 现有字段
  subtotal: number;           // (价格 * 数量) 的总和
  discount?: {
    code: string;
    type: string;
    amount: number;           // 优惠金额（单位：分）
  };
  total: number;              // subtotal - discount
}
```

#### 2.3 购物车过期

- 30 分钟内无活动的购物车应标记为过期
- 过期的购物车不能修改
- `POST /carts/:cartId/refresh` - 延长购物车有效期 30 分钟

### 交付物
- [ ] 添加/更新时检查库存
- [ ] 优惠码支持
- [ ] 购物车过期逻辑
- [ ] 测试通过：`npm test -- --grep "Stage 2"`

---

## 第三阶段：多地区与协作（高级）

**请在完成第二阶段后再阅读本节**

### 新增需求

#### 3.1 多币种支持

提供了汇率服务（见 `src/mocks/exchange-rate.service.ts`）。

- 用户可以用不同币种查看购物车
- `GET /carts/:cartId?currency=EUR` - 以指定币种查看购物车
- 所有金额以请求的币种显示
- 原始价格以美元（分）存储

#### 3.2 共享购物车

多个用户可以协作编辑同一个购物车：

| 接口 | 描述 |
|------|------|
| `POST /carts/:cartId/collaborators` | 通过邮箱邀请用户 |
| `DELETE /carts/:cartId/collaborators/:userId` | 移除协作者 |
| `GET /carts/:cartId/collaborators` | 列出协作者 |

规则：
- 购物车所有者可以邀请协作者
- 协作者可以添加/移除商品，但不能结账或删除购物车
- 处理并发修改（两个用户同时修改）

#### 3.3 保存的购物车与心愿单

| 接口 | 描述 |
|------|------|
| `POST /carts/:cartId/save` | 将购物车保存为命名列表 |
| `GET /users/:userId/saved-carts` | 获取用户保存的购物车 |
| `POST /carts/:cartId/restore/:savedCartId` | 恢复保存的购物车 |

恢复模式：
- `merge` - 将保存的商品添加到当前购物车
- `replace` - 用保存的商品替换当前购物车

处理：保存的购物车引用了已下架的商品

#### 3.4 结账准备

| 接口 | 描述 |
|------|------|
| `POST /carts/:cartId/checkout` | 发起结账 |
| `DELETE /carts/:cartId/checkout` | 取消结账 |

结账流程：
1. 验证所有商品以当前价格可用
2. 在结账期间锁定购物车（5 分钟超时）
3. 如果使用非美元币种查看，锁定汇率
4. 如果验证失败，返回详细错误：

```typescript
interface CheckoutValidation {
  valid: boolean;
  errors?: Array<{
    productId: string;
    issue: 'out_of_stock' | 'insufficient_stock' | 'price_changed';
    details: {
      requested?: number;
      available?: number;
      oldPrice?: number;
      newPrice?: number;
    };
  }>;
  lockedUntil?: Date;
  exchangeRate?: { from: string; to: string; rate: number; };
}
```

### 交付物
- [ ] 多币种支持
- [ ] 带冲突处理的协作购物车
- [ ] 保存/恢复功能
- [ ] 结账验证和锁定
- [ ] 书面说明：你如何处理并发修改？
- [ ] 书面说明：如果需要处理 10,000 次结账/分钟，什么会出问题？
- [ ] 测试通过：`npm test -- --grep "Stage 3"`

---

## 开始使用

```bash
npm install
npm run dev      # 在端口 3001 启动开发服务器
npm test         # 运行所有测试
npm test -- --grep "Stage 1"   # 只运行第一阶段测试
```

## 项目结构

```
src/
├── index.ts                    # 应用入口
├── types.ts                    # TypeScript 接口（所有阶段）
├── routes/
│   └── cart.routes.ts          # API 路由（在此实现）
├── services/
│   └── cart.service.ts         # 核心逻辑（在此实现）
├── storage/
│   └── memory.store.ts         # 内存存储
└── mocks/
    ├── inventory.service.ts    # 模拟库存（第二阶段+）
    ├── exchange-rate.service.ts # 模拟汇率（第三阶段）
    └── products.ts             # 示例商品数据
```

## 评分标准

| 阶段 | A | B | C |
|------|---|---|---|
| 1 | API 设计清晰，错误处理完善，验证到位 | API 可工作，结构合理 | 能工作但代码混乱 |
| 2 | 处理所有边界情况，库存策略清晰，优惠逻辑正确 | 处理大部分情况，有小问题 | 正常流程可工作，边界情况失败 |
| 3 | 并发方案可靠，权衡分析诚实，重构干净 | 方案可工作，有些竞态条件 | 功能拼凑，明显的竞态条件 |
