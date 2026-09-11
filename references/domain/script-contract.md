# 创作稿契约入口

完整脚本的内容中心是 Markdown 创作稿，具体格式和所有权见 [script-workbook-contract.md](script-workbook-contract.md)。脚本不再拆成一份机器 JSON 和一份人类渲染视图。

创作稿修订号、TTS/ASR 引用、段落内容和生成结果链接构成一次可审阅的创作版本。Prompt、请求参数、素材映射、结果和重试状态属于 [execution-record-contract.md](execution-record-contract.md)，由执行适配器自动生成。

Feishu 仍可作为产品、资产和人工审核的远程表面；它不承担第二份动作脚本。创作稿修改后，受影响的执行记录必须失效并重新准备。
