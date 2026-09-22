# Archive evidence

The benchmark and waited worker completed successfully. Main raw/native/source archives were verified from their complete downloaded bytes against remote before/after SHA records. An independently reviewed local validator accepts the source-generated `campaign-plan.json` in addition to the original manifest; the original failed validation receipt remains preserved.

| Archive | Compressed bytes | SHA256 |
|---|---:|---|
| c2-w4a16-megamoe-autotune-20260921-recovery8-raw.tar.gz | 133440132 | `275ddba1a64c2e8c8e37184c4f51a0f0bb130972538d336d7ba6614db72967c9` |
| c2-w4a16-megamoe-autotune-20260921-recovery8-caches.tar.gz | 194131428 | `fd5048c6e317fc73080a83a83bd275d6760f675331e5e82bb119f61c9a1c484e` |
| sources/dependency-0.tar.gz | 12354717 | `087e3e60e1688611044c7875e5b7ac8e9fa395d1ecca39a1a5d32e9c59bbbd9f` |
| sources/dependency-1.tar.gz | 39366434 | `6d7b92365f1a1bbb82e4488487cbc062088abfd8b6f8055c77388260f879cae3` |
| sources/dependency-2.tar.gz | 269092 | `13ccbed676d7ad182de9e72e3af6e78ed53a59950c81fa4c5a455504d42b4840` |
| sources/flashinfer.tar.gz | 30798715 | `5285d50645581d7f0f2c6b62f1939831bc158c5275dc92ea3c092d6999e25169` |
| sources/inferencex.tar.gz | 7449405 | `db109815d3b208b616dc203bda8a091ddd0e64c31f54347698bdff3ff0a8715d` |
| sources/sglang.tar.gz | 33325803 | `586ff5d409deef08229e543c59a0fc48c8d6a54eee168d21c7e716cc1ae354d1` |
| supplemental ephemeral-selected.tar.gz | 8708776 | `ff8029ab23f8b30d1237023ba367b6e4819051643a72738271a3d5f6c28e6100` |

The main raw archive has 4,725 regular members and 63 directory entries, including the 14 finalized cases, their raw14 records, all per-rank native records, original recipe/source receipts, and the full owned-process ledger. The six source archives total 123,564,166 bytes. The two reused Mega cases and all historical controls retain their separately audited original bytes.

Supplemental selection contains 134 ephemeral regular files / 13,318,479 bytes copied locally; 69,437 persistent regular files / 5,555,117,695 bytes remain on Weka with full selected-file SHA records, including all 636 required retained descriptors from the earlier native-build preservation. Thirty-six symbolic links are recorded as metadata only, with all targets already enumerated in the same selected inventory. No directory link is followed or duplicated in the archive. Absent selected leaves are explicitly recorded, including optional `/usr/tmp`.

The supplemental tar contains 136 exact members: the 134 file payloads plus inventory and link metadata. Its uncompressed member payload total is 41,452,858 bytes; this differs from the compressed archive size above. Persistent retention is not a claim that those bytes were also copied locally. The 47-shard model has verified revision/config/index/shard sizes, not a newly computed full tensor-content SHA. No source, checkpoint or persistent cache deletion is part of resource cleanup. Ephemeral data on older disappeared devboxes that was not collected before disappearance is not claimed preserved.

Full task-local archive receipts are retained with the owning workspace; large archive payloads and model weights are not embedded in this Git report. Public per-case raw/native records, source pins, reproducible plot inputs and their hashes are included in the report.

中文：主raw/native/源码归档与补充临时缓存分别校验。持久Weka数据按清单保留并校验，不能将保留证明写成本地副本；模型只声明已有元数据/分片大小验证，不声称新做了完整权重SHA。所有历史失败和原始校验失败均保留。
