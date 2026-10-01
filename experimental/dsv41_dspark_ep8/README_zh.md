# DeepSeek-V4.1 DSpark EP8 实测基准

[English](README.md)

本手动配方复用已有 GLM 串行 runner、按进程出生身份清理、证据封存、随机请求生成、
原生计数归约、离线 reader 与 Pareto 绘图，不安装软件、不下载模型、不提交任务，也不声明 GPU 验证完成。

- **矩阵：** TP=EP=attention DP=8，target 分别使用 MegaMoE W4A4、MegaMoE W4A16 和
  传统 TRTLLM W4A4（`flashinfer_trtllm_routed`/A2A `none`，保留 DeepSeek 原生 routing），C2/4/8/16/32/64。先执行三个后端的 C2 作为正式实测资格验证点，
  再按后端执行 C4–64；共18点、3,780条测量请求和756条计划预热。任一点失败即停止。
- **环境与权重：** 示例固定 SGLang PR head `29c2b32d7f7351082168e622a4747bcff6469271`、
  FlashInfer `a03f2205263d4e691d68e485bff287e37a19b6c3`、原9月30日镜像及 checkpoint
  `3431dde3247c13b5957f682b1e3c6fcae2566079`。源码必须与声明的 clean commit 一致；
  FI 从已安装 main/cubin wheels 导入。环境恢复单独进行。
- **DSpark：** target、内置 draft、tokenizer 共用原始 checkpoint，gamma5/验证宽度6。
  target 为混合量化（NVFP4 routed experts，dense 保持自身精度）；draft 保留原生
  MXFP4/MXFP8，三个后端都使用 `flashinfer_mxfp4`/A2A `none`，不转换成 BF16。
- **默认设置：** 不继承 GLM parser、DSA、KV dtype 或 modelopt 参数。保存实际解析的
  attention/KV/quantization 设置；显式启用 DP LM head、static ragged verify。
  W4A16 仅启用已有 selector；不设置额外 per-token/fast-math 覆盖。实际 kernel/精度/拓扑需另行审核。
- **负载：** 名义输入1024/输出8192、ratio0.8、seed0、每点2C预热/10C测量，greedy、
  ignore EOS、无限到达率、stream interval30。预热按计划发出并等待，但沿用的客户端不逐条
  强制预热成功；所有测量请求必须成功。保持现有并行预处理；相同 C 的各后端必须
  完整匹配有序的请求/完成长度。
- **Prompt：** `--dsv41` 使用固定哈希的模型 `encoding/encoding.py`，显式
  `thinking_mode="chat"`、`reasoning_effort=None`，拒绝多模态数据；不复用旧 `--dsv4`
  隐式 thinking 模式。原 GLM 使用其 tokenizer chat template/add_generation_prompt；
  这里复用采样方法，而非 GLM 的 prompt 字节或 tokenizer。
- **统计：** AL=`sum(completion_tokens)/sum(spec_verify_ct)`，包含原生 bonus token，
  仅计全部成功测量请求；rate=`sum(correct)/sum(proposed)`，其中原生 DSpark 的
  proposed=`5*verify_count` 是配置 proposal budget，不是实际 ragged 验证槽位数。
  任一请求缺少有效原生计数则失败；预热、server lifetime/window 均不计入。
- **性能与范围：** x=`1000/已保存 median TPOT`；y=`总输出token/完整测量时间/8`。
  保留已保存标量，不重建缺失的逐请求延迟/百分位；ITL 是流式 chunk 间隔。不代表质量或因果结论。
- **存储与清理：** 新建独占 HOME/TMP/编译/tactic 路径，无 cache seed；仅本轮共享编译缓存，
  后端 tactic 分开。仅清理已记录出生身份的进程，客户端成功不等于服务端优雅退出。
  完整日志/原始计数/归档保留本地，只发布紧凑表格、图、provenance 与重放代码；旧 GLM 结果不改写。

可复制命令见 [英文页](README.md)。`preflight.py` 必须传入独立的短 `--tmp-root`，仅导入/解析配置，不加载模型或验证分布式 kernel。
`results.py` 要求原始封存证据；`render.py` 只需要紧凑表格，重放算术和图，不代表原始证据验收。
本 experimental 配方尚未注册到 scheduled matrix 或 eval。
