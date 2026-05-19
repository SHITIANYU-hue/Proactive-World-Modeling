# PIWM 项目进度报告

更新时间：2026-05-17 CST

## 1. 一句话总结

项目当前状态：**可按强主会故事推进，但实验结果仍是硬缺口**。数据体系已经从“零散 synthetic 数据”整理成 “general 导购语料 + target 前置摄像头语料 + 评估入口” 三层结构；当前论文口径不再依赖 300+ target 视频，而是强调低资源 target specialization：用 88 条 target 训练样本适配，用 30 条项目负责人 QA 复核样本做 in-domain test。

## 2. 核心进展

1. **主训练数据已经稳定成 v2.2 格式。**  
   `PIWM-Train-Synth-v2` 现在有 543 条父样本、2554 条 ms-swift 训练样本。ms-swift 是训练框架需要的对话式 JSONL 格式，可以理解成“喂给模型的一行行练习题”。

2. **target 域数据已经接入主项目。**  
   `PIWM-Target-Frontcam-v1` 现在有 118 条设备前置摄像头样本、354 张抽帧图、708 条训练样本。这里的 target 指智能售货柜/终端视角，不是普通第三人称导购视角。

3. **30 条 target test QA 已完成并并入数据。**  
   QA 是 Quality Assurance，意思是质量复核：检查三张抽帧图是否看得清顾客、动作标签是否合理、时间顺序是否一致。现在 30 条测试样本全部通过：30 pass / 0 fail / 2 warning。结果已写回 target 主数据和 target 训练 JSONL；88 条训练样本仍标为未人工 QA。

4. **target 扩展队列已经准备好，但还不是视频数据。**  
   `PIWM-Target-PromptReady-v1` 有 318 条 prompt-ready 记录，其中 118 条已有视频，新增 200 条只有 seed / manifest / label / prompt，尚未生成 Kling 视频和抽帧。不能把这 200 条写成多模态训练数据。

5. **domain specialization 实验入口已经齐。**  
   现在已有 general 训练入口、target 训练入口、general+target joint baseline 入口，以及 target QA eval 入口。下一步可以跑 zero-shot、target-specialized、joint baseline 三组结果。

## 3. 需要你关注或决策的事项

1. **论文口径已经确定为强主会故事。**  
   当前不再以 target 视频规模为核心卖点，而是以“general -> target 的低资源专项适配”为核心卖点。118 条 target 视频不是短板本身，真正需要补的是训练和评测结果。

2. **Greet(close) 的三张图解释。**  
   有些 Greet 样本第三张图里顾客已经笑了。当前数据把三张图当作“当前观察状态”，不是“Greeting 之后造成的反应”。所以这类样本可以用于判断“现在适合 Greet(close)”，但不能用于证明“Greet 导致顾客笑”。

3. **下一轮训练资源。**  
   需要决定是否立刻跑：Stage-1 general SFT、Stage-2 target SFT、joint baseline。没有这些跑分，论文实验部分还不完整。

## 4. 整体进度

**已完成**

- 动作空间统一到 6 个 DialogueAct，也就是 6 类元动作：Greet、Elicit、Inform、Recommend、Reassure、Hold。
- 主训练数据 v2.2 独立导出完成：543 父样本 / 2554 训练行。
- target 数据导入完成：118 records / 708 训练行。
- 30 条 target test QA 复核完成并并入 target 数据。
- 318 条 target prompt-ready 队列完成，其中 200 条等待视频生成。
- 文档入口已经收敛到 `docs/README.md` 和 `data/official/DATASET_MANIFEST.json`。

**进行中**

- domain specialization 训练与评测。

**未开始**

- Stage-1 / Stage-2 / joint baseline 三组正式训练。
- zero-shot、target-specialized、joint baseline、forgetting check 四类评测。

**对比原计划**

数据格式和文档整理基本按计划完成；训练与论文实验证据延后。此前把 200 条 pending 视频视为强主会必要条件，现在口径已调整：不生成 200 条视频也可讲强主会，但必须尽快补齐 general-to-target 的训练和评测结果。

## 5. 关键风险

1. **target 数据规模会被 reviewer 追问。**  
   应对不是临时追 200 条视频，而是把问题定义成低资源 domain specialization：88 条 target train + 30 条 QA target test，重点证明少量 target 数据能带来明确迁移收益。

2. **训练结果未落地。**  
   现在有数据入口，还没有新 SFT 和 eval 结果。应对：先跑 general-on-target zero-shot，再跑 Stage-2 target specialization。

3. **因果解释风险。**  
   三张图是当前观察，不是动作后的未来反应。应对：报告和论文中明确区分“当前状态判断”和“动作导致的未来反应”。

## 6. 下一步

1. 跑 Stage-1 general SFT。
2. 跑 Stage-2 target SFT。
3. 跑 joint baseline。
4. 输出 zero-shot、target-specialized、joint baseline 和 general forgetting check 结果。
5. 把结果写入 EMNLP 数据与实验部分。
