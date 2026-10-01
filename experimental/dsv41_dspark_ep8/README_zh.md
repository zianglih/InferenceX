# DeepSeek-V4.1 DSpark EP8 实测基准

[English](README.md)

本手动配方复用已有 GLM 串行 runner、按进程出生身份清理、证据封存、随机请求生成、
原生计数归约、离线 reader 与 Pareto 绘图，不安装软件、不下载模型、不提交任务，也不声明 GPU 验证完成。

所有三个后端均显式传入 `--json-model-override-args '{"vision_n_layers":0}'`，仅改变内存中的 V4.1 配置；原始 checkpoint 文件（包括视觉权重）全部保留。未构建视觉塔时，现有 loader 跳过视觉塔、aligner、image 参数和 VL 路由 bias；文本路由保留普通 bias，内置 DSpark stage 本身已禁用视觉。视觉专用的 Engram/image-token 处理也被禁用；不声明多模态或生成 image token 时的等价性。采样器抽取基础词表 ID，image marker 属于 added token，固定 encoder 会拒绝用户文本中的 image placeholder 或媒体。预检记录并要求 target/draft 均为零视觉层且非多模态。该 pin 的 `--language-only` 是 encoder disaggregation，`--language-model-only` 的架构白名单也不支持 V4.1，因此不使用这两个 flag。原多模态启动在 health 和测量前失败，其源码、配置、运行目录及失败回执保持独立；示例现使用独立的 `mxfp8-fix-v3` 根目录及新短 TMP。

- **矩阵：** TP=EP=attention DP=8，target 分别使用 MegaMoE W4A4、MegaMoE W4A16 和
  传统 TRTLLM W4A4（`flashinfer_trtllm_routed`/A2A `none`，保留 DeepSeek 原生 routing），C2/4/8/16/32/64。先执行三个后端的 C2 作为正式实测资格验证点，
  再按后端执行 C4–64；共18点、3,780条测量请求和756条计划预热。任一点失败即停止。
- **环境与权重：** SGLang 保持 `29c2b32d7f7351082168e622a4747bcff6469271`、原9月30日
  CUDA13镜像和 checkpoint `3431dde3247c13b5957f682b1e3c6fcae2566079`。
  FI 修正后的 Python 源码为 `7a962707af69863d386be2a9bc01ee4607470bcc`，基于
  `a03f2205263d4e691d68e485bff287e37a19b6c3`；已安装 main/cubin metadata 和
  cubin/NCCL wheel payload 保持原构建，不重建、不以源码 `PYTHONPATH` 覆盖 wheels。
  可选 `flashinfer_wheel_commit` 与 `flashinfer_python_patch` 仅允许三个后端统一替换已审
  `flashinfer/gemm/kernels/dense_blockscaled_gemm_sm100.py`。源码快照验证原始 base 与修正 commit
  的 Git blob，provider proof 验证安装模块路径与修正字节。原 SHA 为
  `a07193ecc61c522a1dc26548662524d1cbf27a0b0257888fbb4ca241bd2c7593`，修正 SHA 为
  `a4c20af8ad49c1d050db3dd9b933fa771a4b9d5ca830c5de8a6c66376aa19114`。
  部署和其他 payload 不变需独立验收；这是相对已恢复基线的一项已审修正，
  原 RECORD 与 build metadata 保留不变，包括先前记录的基线例外。省略这两个可选字段时仍要求 source/main/cubin commit 一致。
  新 `mxfp8-fix-v3` run/HOME/TMP 保留两次失败证据；源码检查不代表 GPU/kernel 或性能验收。
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

附带的 [kernel patch](flashinfer-mxfp8-support.patch) 收紧 FP8 tactic 的支持域：
tile N 小于64且逻辑 N 大于该 tile N 的 FP8 tactic 不再参与选择。该条件是保守的支持域限制，
不代表每个被拒绝形状都已复现故障；FP4 eligibility 不变。
[英文页](README.md) 给出从原 a03 commit 应用 patch、记录新源码 commit、校验原始/修正 SHA
并原子替换固定已安装 Python 文件的完整命令，无需重建或重装 wheel。只能在已停止所有
server 的恢复环境中、PREP 前执行；运行期间不得替换。配方本身不会应用 patch。
原安装文件和安装回执保留在本地归档；复现者的 commit metadata 可能不同，必须在配置中
记录实际 clean commit/root，源码与已安装文件的两组 SHA 检查仍是必需项。provider metadata
继续表示原 wheel 身份，不冒称全部 provider 都来自修正后的 Python commit。
