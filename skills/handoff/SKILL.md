---
name: handoff
description: 将当前对话压缩成一份交接文档，供另一个代理接手。
argument-hint: "下一次会话将用于什么？"
disable-model-invocation: true
---

编写一份交接文档，总结当前对话，让一个新的代理可以继续工作。保存到用户操作系统的临时目录，而不是当前工作区。

在文档中包含一个“建议 skills”章节，建议代理应该调用哪些 skills。

不要重复已经捕获在其他制品中的内容（spec、plan、ADR、issue、commit、diff）。改为通过路径或 URL 引用它们。

遮蔽任何敏感信息，例如 API keys、passwords 或个人身份信息。

如果用户传入了参数，把它们视为下一次会话关注内容的描述，并据此调整文档。
