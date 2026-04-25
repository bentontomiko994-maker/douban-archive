# Douban Archive 发布前本地备份

> 这是写入 Obsidian 的本地 copy 版本，用于在正式发布 GitHub 前保存项目定位、使用说明、风险边界和推广方向。

## 项目名称

Douban Archive / 豆瓣本地备份

## 一句话介绍

一个本地优先的豆瓣个人数据归档工具，帮助用户把自己在豆瓣上的书影音、广播、日记和评价记录导出到本地。

## 核心主张

把你的数字记忆从平台里带回本地。

## 为什么做

豆瓣里保存着很多人的长期精神生活记录：读过什么书、看过什么电影、听过什么音乐、写过什么短评、日记和广播。

这些内容虽然发布在平台上，但它们也是用户自己一点点积累出来的个人记忆。平台可能改版、功能下线、限制访问，甚至有一天逐渐衰退。用户应该拥有一份属于自己的本地备份。

在 AI 时代，这些数据还有新的价值：它们可以帮助 AI 更理解一个人的兴趣、审美、偏好和变化轨迹。

## 当前功能

- 导出图书：读过、想读、在读
- 导出电影：看过、想看、在看
- 导出音乐：听过、想听、在听
- 导出广播 / 记录
- 导出日记
- 导出长评 / 评价
- 导出评分、标签、短评、正文、时间和链接
- 支持 JSON、Excel CSV、Markdown
- 后台导出，关闭弹窗后仍可继续
- 本地运行，不上传数据

## 安装方式

1. 下载项目压缩包并解压。
2. 找到 `extension` 文件夹。
3. 打开 Chrome、Edge、Arc 或其他 Chromium 浏览器。
4. 进入 `chrome://extensions`。
5. 打开 `开发者模式`。
6. 点击 `加载已解压的扩展程序`。
7. 选择 `extension` 文件夹。
8. 在同一个浏览器里登录豆瓣。
9. 点击浏览器工具栏里的 Douban Archive 图标。

## 导出格式建议

- JSON：最适合长期备份和 AI 分析。
- Excel CSV：最适合用 Excel、Numbers、Google Sheets 统计和筛选。
- Markdown：最适合人类阅读、Obsidian 和 GitHub 归档。

推荐正式备份时至少导出 JSON。

## 隐私边界

Douban Archive 只在本地浏览器运行。

它不会：

- 上传导出数据
- 收集密码
- 收集 Cookie
- 发送统计分析
- 把用户数据交给第三方

导出的文件可能包含私人日记、评价和兴趣记录，应妥善保存。

## 合规边界

推荐表达：

> 这是一个本地优先的个人数据归档工具，帮助用户备份自己登录后本来可以访问的豆瓣内容。

避免表达：

- 豆瓣爬虫
- 反爬绕过
- 批量抓取
- 破解限制
- 无视风控

项目坚持：

- 只导出用户自己的数据
- 不绕过验证码
- 不绕过登录或权限
- 不采集他人隐私内容
- 不暗示豆瓣官方授权

## GitHub 发布前清单

不要提交：

- `.pem` 私钥
- `.crx` 打包文件
- `.DS_Store`
- 真实导出的豆瓣数据
- 含个人信息截图
- Cookie、token、密码
- 调试日志

应该包含：

- `README.md`
- `README.zh-CN.md`
- `LICENSE`
- `PRIVACY.md`
- `SECURITY.md`
- `docs/zh-CN/USER_GUIDE.md`
- `docs/en/USER_GUIDE.md`
- `docs/zh-CN/RISK_AND_RELEASE_GUIDE.md`
- `docs/en/RISK_AND_RELEASE_GUIDE.md`

## 私钥说明

`.pem` 是扩展打包私钥，不应该公开。别人如果拿到私钥，可能冒充你的扩展进行打包。

`.crx` 是打包后的扩展文件，不建议放进源码仓库。后续如果需要分发，可以放到 GitHub Releases。

## 开源协议

当前使用 MIT License。

它的优点是简单、开放、便于传播和复用，适合第一阶段扩大影响力。

## 推广方向

### 中文平台

核心方向：

- 数据主权
- 数字记忆备份
- 给自己的精神生活留一份本地档案
- 为未来 AI 个人助手准备数据

示例标题：

- 我突然意识到，豆瓣里存着另一个版本的我
- 把十几年的豆瓣记录备份到本地
- 如果 AI 要懂我，它应该先读读我的豆瓣
- 你的数字记忆，不该只躺在平台里

### 国际平台

核心方向：

- Data sovereignty
- Local-first archive
- Personal cultural memory
- AI-ready personal data

示例标题：

- Take back your Douban data
- Your cultural memory should not be locked inside a platform
- A local-first archive for your Douban history

## 下一步改进

- 增加真正的 `.xlsx` 导出
- 增加断点续传
- 增加本地预览器
- 增加匿名化示例数据
- 增加导出字段字典
- 增加 AI 兴趣画像生成
- 增加 GitHub Pages 项目主页

