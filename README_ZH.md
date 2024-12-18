中文 ｜ [English](./README.md)

<br>
<a href="https://huggingface.co/spaces/jt120lz/open-improve-prompt">Demo</a>

# 简介

这是 [Anthropic 提示增强](https://console.anthropic.com/dashboard)的开源版本，可以切换不同的模型。

## 功能特点

- 支持生成中文和英文
- 多种 LLM 模型选项（DeepSeek、Claude 3.5 Sonnet、GPT-4o）
- 可以下载结果

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

运行应用程序：

```bash
python app.py
```

打开 [localhost](http://localhost:7860) 访问程序。

步骤:

1. 输入要优化的提示语和反馈。
2. 选择要优化的语言：中文或英文。
3. 选择要优化的 LLM 模型：DeepSeek、Claude 3.5 Sonnet、GPT-4o。
4. 点击优化按钮。
5. 等待结果出现。

## 更多信息

- 目前只模仿了anthropic的分析和优化两步，还遗留了example提取，反思，精修步骤，目前已经满足了我的需求，如果使用过程中，不能满足你的需求，可以提交issue，包含待优化的prompt和feedback，我会判断是否需要复刻更多的内容。
- 如果希望支持更多的模型，可以自己做修改，或者提交issue，目前三个模型基本满足需求了。

## 参考资料

- [anthropic文档](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-improver)
- [generate](https://github.com/wangyuxinwhy/generate)
