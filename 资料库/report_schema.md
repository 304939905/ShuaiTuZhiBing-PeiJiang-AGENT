# 学习报告 JSON Schema（gen_report.py 输入格式）

每个视频生成一份 JSON，由 `gen_report.py` 渲染为 Word（9 章节固定结构）。

```jsonc
{
  "video_title": "视频标题（文件名）",
  "video_id": "V001",                 // 视频编号，跨视频累计
  "duration": "00:03:33",            // 来自 ffprobe 的精确时长（MM:SS 或 HH:MM:SS）
  "resolution": "1900x1080",         // 来自 ffprobe
  "has_subtitle_stream": false,      // 来自 ffprobe；抖音视频多为 false（硬字幕）
  "audio_transcribed": true,         // 是否用 whisper 转写音频
  "report_date": "2026-08-07",
  "scope": "完整视频（音频转写 + 逐15秒取帧 + 画面字幕识别）",

  "summary": {
    "what_it_teaches": "本视频真正讲了什么（一句话结论）",
    "core_conclusions": ["结论1", "结论2", "..."],   // 3~6条
    "not_concluded": ["不能得出的结论1", "..."]
  },

  "content_scope": {
    "formal": ["正式讲解的内容"],
    "mentioned": ["简单提及的内容"],
    "preview": ["系列预告/后续选题"],
    "not_covered": ["未讲内容"]
  },

  "knowledge": [                     // 核心知识详解，按逻辑主题分组
    {
      "topic": "主题名（如：资源发育）",
      "points": [
        {
          "text": "知识点（先结论后理由）",
          "time": "00:01:23",        // 视频时间点
          "evidence": "旁白/字幕/画面",
          "confidence": "明确/推断/无法确认",
          "shot": "图3"             // 可选，引用 screenshots 的 id，就近插图
        }
      ]
    }
  ],

  "cases": [                         // 视频案例分析
    {"title": "案例名", "time": "00:02:00", "proves": "证明什么", "not_prove": "不能证明什么"}
  ],

  "actionable": [                    // 可执行方法（检查流程/配将步骤/判断清单）
    {"step": "步骤", "detail": "说明"}
  ],

  "pitfalls": ["常见误区1", "常见误区2"],
  "unknown": ["查不到/无法确认的内容1"],

  "evidence_index": [                // 来源与证据索引（表格）
    {"conclusion": "结论", "time": "00:01:23", "screenshot": "图3", "confidence": "明确"}
  ],

  "screenshots": [                   // 截图，必须来自当前视频，标注时间点
    {"id": "图1", "time": "00:00:15", "path": "绝对路径.jpg", "caption": "只描述画面真实内容"}
  ]
}
```

## 信息分类要求（写入正文时遵守）
- A 视频明确说明（旁白/字幕/画面）→ 直接写正文
- B 根据画面推断 → 必须标注“根据画面推断”
- C 外部补充 → 单独“外部补充”节并注明来源/日期/版本（本 schema 暂未单列，可放 unknown 或 evidence_index 注明）
- D 查不到/无法确认 → 写“查不到/不知道/无法确认”，禁止猜测

## 配将/战法专项（knowledge.points 中须分别核对）
武将位置（大营/中军/前锋）、普攻距离、战法有效距离、战法目标数、目标类型、发动条件/准备回合、增距/增伤/生存/控制取舍、战报实际命中位置。不得混淆普攻距离与战法距离。
