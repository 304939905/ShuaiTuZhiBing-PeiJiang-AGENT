from legacy_version_evidence import extract_legacy_builtin_evidence


def main() -> None:
    data = {
        "summary": {"visual_only": ["杜预「三军夺帅」战法杀伤 19015。"]},
        "frame_only_value": ["完整阵容：祝融夫人（蛮兵/火兽冲锋+先驱突击+三军齐出）。"],
        "timeline": [{"frames": [
            {"file": "frame_001.jpg", "desc": "荀彧带「驱虎吞狼」，郭嘉带「奇佐鬼谋」。"},
            {"file": "frame_002.jpg", "desc": "荀彧与贾诩之间夹杂大量文字，再说驱虎吞狼。"},
            {"file": "frame_003.jpg", "desc": "司马懿（其徐如林+神兵天降+久战熟谋）。"},
            {"file": "frame_004.jpg", "desc": "程昱：审时定计 / 焰焚箕轸 / 磐阵善守。"},
            {"file": "frame_005.jpg", "desc": "配队：荀彧（大营）+司马懿（中军）+曹操（前锋），九战法为驱虎吞狼 / 众谋不懈 / 河内世泽、其徐如林 / 神兵天降 / 久战倦怠、魏武之世 / 一夫当关 / 反计之策。"},
            {"file": "frame_006.jpg", "desc": "曹操(前锋)：魏武之世1次杀1723。"},
            {"file": "frame_007.jpg", "desc": "关银屏武将界面，展示自带战法「巾帼战阵」有效距离4。"},
            {"file": "frame_008.jpg", "desc": "红框标注「其徐如林」（司马懿自带S级战法位）。"},
        ]}],
    }
    evidence = extract_legacy_builtin_evidence(data)
    assert {"builtin_skill": "驱虎吞狼", "anchor": "frame_001.jpg"} in evidence["荀彧"]
    assert evidence["郭嘉"] == [{"builtin_skill": "奇佐鬼谋", "anchor": "frame_001.jpg"}]
    assert evidence["杜预"] == [{"builtin_skill": "三军夺帅", "anchor": "summary.visual_only[0]"}]
    assert {"builtin_skill": "其徐如林", "anchor": "frame_003.jpg"} in evidence["司马懿"]
    assert evidence["程昱"] == [{"builtin_skill": "审时定计", "anchor": "frame_004.jpg"}]
    assert {"builtin_skill": "其徐如林", "anchor": "frame_005.jpg"} in evidence["司马懿"]
    assert {"builtin_skill": "魏武之世", "anchor": "frame_005.jpg"} in evidence["曹操"]
    assert {"builtin_skill": "魏武之世", "anchor": "frame_006.jpg"} in evidence["曹操"]
    assert evidence["关银屏"] == [{"builtin_skill": "巾帼战阵", "anchor": "frame_007.jpg"}]
    assert {"builtin_skill": "其徐如林", "anchor": "frame_008.jpg"} in evidence["司马懿"]
    assert evidence["祝融夫人"] == [{"builtin_skill": "火兽冲锋", "anchor": "frame_only_value[0]"}]
    print("legacy_version_evidence: PASS")


if __name__ == "__main__":
    main()
