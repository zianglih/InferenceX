# Recovery3：恢复 FlashInfer 源码资源布局

[English](RECOVERY3.md) | **中文**

Recovery2 在测量前停止：新 FlashInfer checkout 缺少
`flashinfer/data/csrc/.../fp4Quantize.cpp`。固定提交中的原始文件存在，但 editable
安装通常生成的、被 Git 忽略的资源链接没有创建。Recovery3 使用新根目录和 run ID，
保留前两次失败证据，以及 recovery1 两个已接受结果。

- **保持不变：** SGLang `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2`、FlashInfer
  `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`、镜像、已安装包清单、模型、`.80`、
  TP=DP=EP、原生 BF16 TRT-LLM MTP 和全部客户端设置。
- **准备阶段修复：** 注册固定 CCCL/CUTLASS/spdlog gitlink，从 recovery1 复制独立 Git
  对象。在新 `flashinfer/data` 下只创建 `cutlass`、`spdlog`、`cccl`、`csrc`、
  `include` 五个链接，目标全部位于新 checkout。显式生成固定 `_build_meta.py`，
  不导入 `build_backend`，不运行 pip。对照 Git 校验十一项源码/头文件，包括 FP4
  量化的全部七个编译单元；另验证实际导入的 metadata 和 JIT csrc 路径属于新源码。
- **证据：** 初始 setup seal 同时包含三个主仓库和三个依赖的 Git 归档、资源布局及
  sentinel 哈希、生成的 metadata、导入记录、helper、前后 runtime/freeze 和
  recovery2 终止回执。launch 和 worker 入口再次检查资源布局与源码清洁状态，
  无需事后补依赖 appendix。
- **缓存：** 只从 SHA 封存的 recovery1 缓存清单复制到新目录，保留旧字节并重映射
  其内部链接。此续跑不使用 recovery2 的缓存，也没有 recovery2 成功点可复用。
- **剩余矩阵：** 8k1k 的 TP4 C8/16/32/64/128、TP8 C4；1k1k 的 TP4
  C256/4/8/16/32/64/128、TP8 C4。十四个新点要求 7,640 个成功请求；原样引用
  recovery1 C256/C4 的 2,600 个请求。只有独立组合验收后才能称为 16 点、10,240
  个成功请求；不重写旧结果 metadata。

新 helper 私有复用 SHA 固定的 recovery2 缓存复制、旧结果引用校验、矩阵门槛和归档
实现。Recovery2 与原完整 sweep 成功门槛保持原样。benchmark 非零退出只会形成失败
归档，`complete_matrix: null`，不会被当作成功。

本 recipe 审查、提交并推送后，调用方必须提供完整已发布 commit。在已审查节点
`hu-pdx-126` 上运行；prepare 要求八张 B300 空闲、前两个 worker 已终止、已安装包及
runtime 不变、目标目录不存在。prepare 不会启动 benchmark；失败准备会保留且拒绝覆盖。

```bash
# 通过已批准节点的 dispatch，使用新提交中逐字一致的 helper。
python3 -B continue_megamoe_recovery3.py prepare --recipe-commit FULL_PUBLISHED_SHA

# 审阅 environment/setup-completed.json 后单独 launch。
python3 -B /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery3/sources/inferencex/experimental/glm52_b300_fixed_seq/continue_megamoe_recovery3.py launch
python3 -B /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery3/sources/inferencex/experimental/glm52_b300_fixed_seq/continue_megamoe_recovery3.py status
```

后台 worker 等待 benchmark 结束，写入 benchmark 退出回执，封存 raw/environment/source
及 cache 归档，再写 worker 退出回执。launch 为独占操作，不自动重试。run ID 为
`c2-w4a16-megamoe-autotune-20260921-recovery3`。收集和校准必须使用另行审查的 recovery3
consumer；recovery2 consumer 不能证明 recovery3 已通过。本地 fixture 只验证准备流程，
不代表 GPU 或性能结果。
