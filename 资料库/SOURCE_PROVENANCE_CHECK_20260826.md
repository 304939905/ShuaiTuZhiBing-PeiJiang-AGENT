# 来源可追溯性自动检查

- JSON 母本：72
- DOCX 报告：68
- ERROR：0
- WARN：6

说明：检查器不能从当前文件快照推断历史上是否删除过来源；未来删除必须写 `source_deletions`，并包含 `source` 和 `reason`。

## 发现

- [WARN] `EXTERNAL_NAME_NO_URL`：`D:\Desktop\shandou\资料库\frame_json\高顺领衔群骑，来了！ 8回合高频解控，四重增伤，非常均衡的一队。.json` — 提到外部站点但未给可复现 HTTP(S) 直链
- [WARN] `EXTERNAL_NAME_NO_URL`：`D:\Desktop\shandou\资料库\frame_json_kaihuang\video_率土开荒焚诀，【开荒的基本原理】..._top_0_2.json` — 提到外部站点但未给可复现 HTTP(S) 直链
- [WARN] `EXTERNAL_NAME_NO_URL`：`D:\Desktop\shandou\资料库\frame_json_kaihuang\开荒期常见问题汇总 ，一篇全看懂，兄弟们速速来看！.json` — 提到外部站点但未给可复现 HTTP(S) 直链
- [WARN] `EXTERNAL_NAME_NO_URL`：`D:\Desktop\shandou\资料库\hzh_frame_json\也是挨抓一回.json` — 提到外部站点但未给可复现 HTTP(S) 直链
- [WARN] `EXTERNAL_NAME_NO_URL`：`D:\Desktop\shandou\资料库\hzh_frame_json\尝试搭建祝融马谡后手刀.json` — 提到外部站点但未给可复现 HTTP(S) 直链
- [WARN] `EXTERNAL_NAME_NO_URL`：`D:\Desktop\shandou\资料库\saiji_frame_json\最强四星0氪蜀之智，萌新玩家必看.json` — 提到外部站点但未给可复现 HTTP(S) 直链
