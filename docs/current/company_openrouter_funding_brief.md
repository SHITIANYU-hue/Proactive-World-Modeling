# PIWM 实验进度与 OpenRouter 预算（精简版）

更新时间：2026-05-01 CST

本文是 [`company_data_status_for_openrouter.md`](company_data_status_for_openrouter.md) 的**摘要**，口径与完整版一致；需要数据路径、主表与消融数字时请打开完整版。

---

## 进度（一句话）

已完成「合成视频 → 抽帧 → QA → 结构化数据 → Qwen2.5-VL LoRA SFT → 评测」第一轮闭环；项目处在**有数据、有训练、有结果**的阶段，而不是纸面方案。

## 数据（摘录）

| 类型 | 规模 |
|---|---:|
| 合成 parent 视频训练集 | 260 |
| SFT 样本（当前主 checkpoint） | 1321 条 |
| 行为 QA 评测 | 40 审 / 36 通过 |
| Future Verification（pilot） | 84 对 |
| 500 / 1000 parent 扩展 | 队列已就绪 |

## 模型（第一轮）

相对原始 Qwen2.5-VL：**结构化可解析输出**从不稳定到评测集上 **100%**；**购买阶段**约 **88.9%**；**候选动作**约 **75.0%**；**动作后果（风险/收益等）**由约 **26%–37%** 提升到约 **99%–100%**。详细分项与附录主表见完整版。

## 边界（对外要说清）

适合 **Demo / POC**，不宜承诺 **无人值守** 上线：QA 评测仍需扩容，状态与候选动作仍是短板，且目前只系统验证了**一条**主基座。

## 为什么要 OpenRouter

在同一套数据与评测协议下做 **多模型横评**，选出效果—成本最适合产品化与论文的基座。

```text
不是验证 PIWM 能不能做，而是找出 PIWM 应该基于哪个 VLM 做得最好、最便宜、最适合产品化。
```

**候选方向（本轮不优先 Claude）：** GPT-4.1 Mini / GPT-4o Mini；Gemini 2.5 Flash / Flash Lite；Qwen3-VL 与 Qwen2.5-VL 大规格；GLM-5V / GLM-4.xV；Kimi / Seed / MiniMax 等作低成本扩展。DeepSeek 偏文本，不作多图视觉主评。

## 建议额度（务实）

视觉样本约 **380** 条 × **6–8** 个模型 ≈ **2280–3040** 次调用量级。**推荐申请 $150–$200**；偏保守至少 **$50** smoke；若要多国产 + top 复测可按 **$300** 预留。（档位表与产出清单见完整版第六节。）

## 英文一句（可选）

```text
PIWM has completed an end-to-end synthetic data and evaluation loop for proactive in-store assistance. Additional OpenRouter budget will fund controlled multi-model comparison under the same QA-reviewed protocol to select the best foundation model before larger-scale data expansion.
```
