#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调用视觉模型识别本地图片。多 Provider 备用, 每模型仅询问 1 次, 无结果立即切下一个。
Provider 顺序(2026-08-21 用户指令: 视觉优先 gpt-5.6-terra; 智谱免费已弃用):
  0) Superoute(视觉首选, 2026-08-21 用户接入, 走代理): gpt-5.6-terra(实测准, 4色框识别好) -> gpt-5.5 -> gpt-5.4
     -> claude-opus-4-8 -> claude-sonnet-4-6 -> claude-haiku-4-5 -> gemini-3.5-flash -> gemini-3.1-pro
     注: luna 实测 tier 不可用(HTTP 400) 已剔除; mini 质量差(武将名错字/位置当词条) 已剔除
     -> gemini-3.1-flash-lite(实测准快) -> doubao-1-5-vision-pro-32k
     -> gpt-5.1 -> gpt-4.1 -> claude-sonnet-4-6 -> gpt-5.2 -> gemini-2.5-pro
     -> gemini-3-flash-preview -> gemini-flash-latest -> glm-4.5v
     注: 2026-08-21 实测 GPT 5.5/5.6-luna/5.6-terra/5.4 全线 503 限流(当日)
  2) 阿里云百炼(兜底/交叉核验): qwen3-vl-plus -> qwen3-vl-flash -> qwen-vl-plus
  3) 商汤日日新(免费兜底): sensenova-6.8-flash-lite(多模态, 每5小时1500次)
     提示词要点(宝物布局): 宝物名=宝物图标右侧大字, 宝物词条=宝物名正上方紧邻小字, 兵种词条=宝物下方小字
     实测: qwen3-vl-plus/flash 按此提示词识别准确; 不提示会上下颠倒
  3) 商汤日日新(免费兜底, 2026-08-21 用户接入): sensenova-6.8-flash-lite(多模态, 每5小时1500次)
已剔除(不适用): gemini-3.5-flash(内容异常) / DeepSeek-OCR-2(循环输出) / gemini-3-pro-image(生图模型不能识图, 400)
                  / qwen-vl-ocr(输出格式乱) / qwen-vl-max(识别有错字)
已弃用: 智谱免费系列(glm-4.6v-flash/glm-4.1v-thinking-flash/glm-4v-flash, 用户 2026-08-21 指令移除, 阿里云兜底)

**4 色框位置规则（2026-08-21 用户定版，用于阵容弹窗识别提示词）**：
  🔴 红框 = 宝物名（宝物图标右侧大字，无 = 空槽）→ gear
  🟢 绿框 = 宝物词条（宝物名正上方小字，不一定有）→ traits
  ⚠️ **宝物词条识别仅做参考，置信度低，不精细化处理（2026-08-21 用户规则）——读不清直接留空，不做交叉核验**
  🔵 蓝框 = 兵种词条（宝物栏下方/武将卡旁小字，不一定有但通常有）→ unit_traits
  🟡 黄框 = 无宝物时空槽（仅武将没带宝物时，gear=null）
  ⚠️ 三层独立不一定齐全；空槽禁编造默认宝物；逐字转录禁止跨框猜测
全部失败时明确报告各模型失败原因。
用法: vision_glm.py <图片路径> [问题文本]
Key 来源(每 provider): 环境变量 > 注册表 HKCU\\Environment > D:\\WorkBuddyData\\secrets\\<name>_key.txt
安全: 不打印 Key; Key 不写入任何项目文档。依赖 requests(浏览器UA, 绕过Cloudflare)。
"""
import sys, os, base64, json, re
import requests

MAX_RETRY = 1          # 每模型仅询问 1 次, 失败直接切下一模型(不等待重试)
BACKOFF = []

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def get_key(env_name, reg_name, file_path):
    k = os.environ.get(env_name)
    if k and k.strip():
        return k.strip()
    try:
        import winreg
        rk = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        try:
            v, _ = winreg.QueryValueEx(rk, reg_name)
            if v and v.strip():
                return v.strip()
        except FileNotFoundError:
            pass
        finally:
            winreg.CloseKey(rk)
    except Exception:
        pass
    if os.path.exists(file_path):
        k = open(file_path, encoding="utf-8").read().strip()
        if k:
            return k
    return None


def call_once(base_url, model, key, data_uri, question, max_tokens=4096, use_proxy=False):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": data_uri}},
            {"type": "text", "text": question},
        ]}],
        "stream": False,
        "max_tokens": max_tokens,
    }
    if use_proxy:
        # 走系统代理(Clash 127.0.0.1:7890)——Superoute 等海外 API 必需
        proxies = requests.utils.get_environ_proxies()
    else:
        # 禁用环境代理(Clash未开时国内 API 连不上), 国内直连
        proxies = {"http": None, "https": None}
    r = requests.post(
        base_url.rstrip("/") + "/chat/completions",
        json=payload,
        headers={"Authorization": "Bearer " + key, "User-Agent": UA},
        timeout=120,
        proxies=proxies,
    )
    if r.status_code != 200:
        raise requests.HTTPError(f"HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    msg = data["choices"][0]["message"]
    content = msg.get("content")
    if not content:
        # 商汤 sensenova-6.8 等模型有时把回答放 reasoning 字段(2026-08-21 实测)
        content = msg.get("reasoning")
    if not content:
        raise RuntimeError("响应无内容: " + json.dumps(data, ensure_ascii=False)[:300])
    return content


def main():
    if len(sys.argv) < 2:
        print("用法: vision_glm.py <图片路径> [问题]")
        sys.exit(2)
    img = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else (
        "请详细描述这张图片的内容：画面主体、UI/文字、武将/卡牌、战报等信息，尽量识别出可见的文字。"
    )
    # 2026-08-21 词条池辅助: 若问题中提及宝物名, 自动附上官网锻造词条池(缩小词条识别范围)
    POOL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gear_forge_pool.json")
    if os.path.exists(POOL_FILE) and ("宝物" in question or "词条" in question or "绿框" in question):
        try:
            pool_data = json.load(open(POOL_FILE, encoding="utf-8"))
            pool = pool_data.get("pool", {})
            # 从问题中提取宝物名（常见于"识别X宝物"或直接命中池key）
            hits = [g for g in pool if g in question]
            if hits:
                hint = "；".join(f"{g}的可用词条池={('/'.join(pool[g]))}" for g in hits[:5])
                question += ("\n【官方参考】画面中可能出现的宝物锻造词条池：%s"
                             "——宝物词条(绿框)只可能是这些词条之一，从中挑选，不要臆造。" % hint)
        except Exception:
            pass
    with open(img, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    ext = os.path.splitext(img)[1].lower().lstrip(".")
    if ext not in ("jpg", "jpeg", "png", "webp", "gif", "bmp"):
        ext = "jpeg"
    data_uri = f"data:image/{ext};base64,{b64}"

    providers = [
        {
            "name": "Superoute",
            "base": "https://api.superoute.uk/v1",
            "key_env": "SUPEROUTE_API_KEY", "key_reg": "SUPEROUTE_API_KEY",
            "key_file": r"D:\WorkBuddyData\secrets\superoute_key.txt",
            "use_proxy": False,  # 2026-08-21 VPN关闭后实测: 直连可用(8s), 代理失效; 直连优先
            # 2026-08-21 用户指令: 视觉模型优先 gpt-5.6-terra(实测准, 4色框识别好)
            # luna 实测 HTTP 400 tier 不可用已剔除; mini 质量差(武将名错字/位置当词条)已剔除
            "models": ["gpt-5.6-terra", "gpt-5.5", "gpt-5.4", "claude-opus-4-8",
                       "claude-sonnet-4-6", "claude-haiku-4-5", "gemini-3.5-flash", "gemini-3.1-pro"],
        },
        {
            "name": "阿里云百炼",
            "base": "https://llm-e28smlmktkm49xyq.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
            "key_env": "ALIYUN_API_KEY", "key_reg": "ALIYUN_API_KEY",
            "key_file": r"D:\WorkBuddyData\secrets\aliyun_key.txt",
            # 2026-08-21 实测: qwen-vl-ocr 格式乱/qwen-vl-max 有错字 已剔除; 智谱免费模型已弃用, 阿里云作兜底
            "models": ["qwen3-vl-plus", "qwen3-vl-flash", "qwen-vl-plus"],
        },
        {
            "name": "商汤日日新",
            "base": "https://token.sensenova.cn/v1",
            "key_env": "SENSENOVA_API_KEY", "key_reg": "SENSENOVA_API_KEY",
            "key_file": r"D:\WorkBuddyData\secrets\sensenova_key.txt",
            # 2026-08-21 用户接入: sensenova-6.8-flash-lite 多模态免费(每5小时1500次), 阿里云后的兜底
            "models": ["sensenova-6.8-flash-lite"],
        },
    ]

    failures = []
    for pi, p in enumerate(providers):
        key = get_key(p["key_env"], p["key_reg"], p["key_file"])
        if not key:
            print(f"[{p['name']} 无 Key, 跳过]", file=sys.stderr)
            failures.append(f"{p['name']}: 无 Key")
            continue
        for model in p["models"]:
            for attempt in range(MAX_RETRY):
                try:
                    print(call_once(p["base"], model, key, data_uri, question, use_proxy=p.get("use_proxy", False)))
                    return
                except requests.HTTPError as e:
                    code = e.response.status_code if e.response is not None else 0
                    if code == 0:
                        # e.response 可能为 None(自定义抛错), 从消息提取 "HTTP <code>"
                        m2 = re.search(r"HTTP\s+(\d+)", str(e))
                        code = int(m2.group(1)) if m2 else 0
                    msg = str(e)
                    if code == 429 or code >= 500:
                        print(f"[{p['name']}/{model} 限流/忙 {code}, 切下一模型]", file=sys.stderr)
                    else:
                        print(f"[{p['name']}/{model} 不可用 HTTP {code}] {msg[:160]}", file=sys.stderr)
                    failures.append(f"{p['name']}/{model}: HTTP {code}")
                    break
                except Exception as e:
                    print(f"[{p['name']}/{model} 异常] {e!r}", file=sys.stderr)
                    failures.append(f"{p['name']}/{model}: {e!r}")
                    break
        if pi < len(providers) - 1:
            print(f"[{p['name']} 全部失败 -> 切下一 Provider]", file=sys.stderr)
    print("FAILED: 所有视觉模型均无结果。失败明细:")
    for f in failures:
        print("  -", f)


if __name__ == "__main__":
    main()

