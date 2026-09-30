# Dependencies and provenance

Planning and recipe validation use Python 3.12+ and the standard library. This R4 recipe additionally requires a separately supplied, unpublished SGLang DP1/SP integration; even dry planning checks its exact local bytes. The public package contains the hash-only source contract, not the patch or three changed SGLang source files. See the README prerequisite before running plan-dependent tests or execution. The explicit runner/preflight uses the already installed, separately validated SGLang/FlashInfer/CUDA environment; these scripts do not install or upgrade it.

The unmodified benchmark client imports NumPy, aiohttp, tqdm and Transformers, with tokenizers/huggingface-hub used by tokenizer loading. The Kimi tokenizer's accepted custom code also requires its own tokenizer dependencies (including tiktoken). Optional branches reference vLLM and ModelScope; using the OpenAI-compatible `vllm` request backend here does not by itself require a vLLM server or package. Validate the selected tokenizer path in preflight. Matplotlib is needed only to render accepted result figures.

Exact serving package versions, compiler/runtime/library origins and GPU identities belong in the actual preflight receipt. No untested dependency resolver invocation is supplied. Reusing the pinned image does not prove every module import or selected kernel is valid.

Vendored client files are exactly those listed in `vendor/inferencex/SOURCE.json`, pinned to InferenceX commit `652ac186d88ebcd6ff995afbe7c3094751f0f4a2`. They remain Apache-2.0, with LICENSE included. The original config/tokenizer reference JSONs identify their public Hugging Face revision in the adjacent receipt; the full model weights and proprietary/local audit artifacts are not part of this package.

## 中文

规划使用 Python 3.12+ 及标准库。R4 还要求单独提供尚未公开的 SGLang DP1/SP 集成；dry plan 也会核验其本地精确字节。公开包只包含哈希契约，不包含补丁或三个 SGLang 源码文件。运行依赖 plan 的测试或执行前，请先满足 README 中的前置条件。执行依赖已安装且单独验证过的SGLang/FlashInfer/CUDA环境；脚本不安装或升级软件。

未修改的客户端使用NumPy、aiohttp、tqdm、Transformers，以及tokenizer路径所需的tokenizers/huggingface-hub。Kimi自定义tokenizer代码还需要自身依赖（包括tiktoken）。vLLM和ModelScope属于可选分支；这里的OpenAI兼容 `vllm` 请求后端不等于需要vLLM服务端或软件包。Matplotlib只用于绘制已验收结果。

实际版本、动态库来源、GPU身份和tokenizer路径由preflight记录。vendor保持SOURCE.json中的固定提交和字节，附带Apache-2.0许可证。参考JSON保留公开Hugging Face来源；完整模型权重及私有审计文件不随包发布。
