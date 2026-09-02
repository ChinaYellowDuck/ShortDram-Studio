# 贡献指南

首先感谢你考虑为 ShortDram Studio 贡献代码！我们欢迎任何形式的贡献，无论大小。

## 📋 行为准则

参与本项目时，请遵守以下行为准则：

- 尊重他人，保持友善和专业的态度
- 接纳不同的观点和经验
-  gracefully 接受建设性批评
- 关注对社区最有利的事情

## 🚀 如何开始贡献

### 1. 报告 Bug

如果你发现了 Bug，请：

1. 先在 [Issues](https://github.com/your-username/ShortDram-Studio/issues) 中搜索，确认是否已有类似问题
2. 如果没有，创建一个新的 Issue，并包含以下信息：
   - 清晰的标题和描述
   - 复现步骤
   - 预期行为和实际行为
   - 你的环境信息（操作系统、浏览器、Node/Python 版本等）
   - 相关的截图或错误日志

### 2. 提出新功能

有好点子？欢迎提交 Feature Request：

1. 在 Issues 中搜索是否已有类似提议
2. 创建新 Issue，标签为 `enhancement`
3. 描述清楚：
   - 你想要什么功能？
   - 为什么需要这个功能？
   - 你期望的使用方式是怎样的？

### 3. 贡献代码

#### 开发环境搭建

```bash
# Fork 并克隆项目
git clone https://github.com/your-username/ShortDram-Studio.git
cd ShortDram-Studio

# 创建功能分支
git checkout -b feature/your-feature-name
```

#### 代码规范

- **前端**: 遵循 ESLint + Prettier 配置
- **后端 (Node.js)**: 遵循 ESLint 配置
- **后端 (Python)**: 遵循 PEP 8 + black + isort
- 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/) 规范

#### 提交 PR 前检查清单

- [ ] 代码通过 lint 检查
- [ ] 所有现有测试通过
- [ ] 为新功能添加了必要的测试
- [ ] 更新了相关文档
- [ ] 代码与项目风格保持一致

#### 提交 Pull Request

1. 推送到你的 Fork 仓库
2. 在 GitHub 上创建 Pull Request
3. 填写 PR 模板，清晰描述你的改动
4. 等待 Code Review

## 🏷️ Issue 标签说明

| 标签 | 说明 |
|------|------|
| `bug` | Bug 报告 |
| `enhancement` | 新功能或改进 |
| `documentation` | 文档相关 |
| `good first issue` | 适合新手的任务 |
| `help wanted` | 需要帮助的任务 |
| `question` | 问题讨论 |
| `wontfix` | 不会处理的问题 |

## 💡 其他贡献方式

不只是写代码，还有很多方式可以贡献：

- 📖 完善和翻译文档
- 🎨 设计 Logo、UI 界面
- 📝 撰写教程和博客
- 🔍 测试并报告 Bug
- 💬 在社区中帮助解答问题

---

再次感谢你的贡献！🎉
