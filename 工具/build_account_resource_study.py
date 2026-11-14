"""Persist authored learning cards for the account/resource reading group.

The decisions below were written after reading the complete source reports.
Local data is evidence of saved descriptions, not a live game verification.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '资料库/策略知识库/精编全量学习_20261011'
GROUP = '01_账号与资源'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rule(condition, decision, reason, failure, paragraphs):
    return dict(condition=condition, decision=decision, reason=reason,
                failure_mode=failure, evidence_paragraphs=paragraphs)


# Each entry contains report-specific reasoning, not title-derived templates.
SPECS = {
    '001': dict(tags=['神赏优先级', '四队共存', '版本消歧'],
        rules=[rule('四队共享单份神兵、大赏、反计，第三队缺战必双减',
                    '先锁第一队法刀资源，再把第三队记为过渡保护结构',
                    '后队配置是前队占用后的剩余解，保护缺口决定适用对手',
                    '拆开抄四队满配，或把过渡魏智当完整双减体系', [9, 10, 34, 35, 36]),
               rule('卡面与战法图标同时有SP/XP角标，或姜维只有自带名称可读',
                    '卡本体标记单独记录；姜维再用兵种、精确ID或初始属性消歧',
                    '列营守险由蜀弓、蜀步共同使用，不能独自锁定版本',
                    '把战法来源角标当武将版本，或凭列营守险判断弓步', [11, 38, 39])],
        resources=['神兵天降、大赏三军、反计之策单份争用', '第三队保护与前后手证据'],
        limits=['S赛季简称不等于具体S1/S2/S3阶段', '同名卡和学习战法来源须分别锁定'],
        excluded=['四队当代强度排名', '第三队在所有对手下都能靠替代保护成立'],
        check='hero_version', refs=[11, 39],
        questions=['实际是S几及何剧本？姜维具体ID、兵种是什么？第三队对手与事件战报是否支持保护链？'],
        related=['055', '057', '060']),
    '005': dict(tags=['候选否决', '稀缺资源', '红度边界'],
        rules=[rule('账号想同时维持三支主力，某一候选红度很高但缺核心',
                    '先否决触发、目标、保护、距离不成立的方案，再比较红度收益',
                    '进阶增强既有链条，不能凭空补足核心触发与合法目标',
                    '用红度替代发动前提，或按作者队伍档位直接录用', [8, 11, 23, 31, 36, 37]),
               rule('候选队争用同一稀缺战法',
                    '比较三队并存时的边际收益和替换代价，再分配资源',
                    '局部最优可能削弱原本完整的第一队',
                    '逐队先写满配，最后才发现不能共存', [10, 26, 32, 39])],
        resources=['觉醒、红度、赛季与当前库存', '单份战法的边际收益及替代成本'],
        limits=['XP标签不独自说明新获取阶段', '候选体系须重查本次账号'],
        excluded=['三套同名阵容的固定强弱档位', '高红直接抵消缺核心'],
        check='rare_counts', refs=[10, 26, 32],
        questions=['哪些战法确实拥有、总份数几份？候选的硬性触发和保护分别是什么？'],
        related=['007', '042', '045']),
    '006': dict(tags=['主力与工具队', '过渡退出', '投入集中'],
        rules=[rule('旧卡红度较好，但现代核心不足、第五队只能执行辅助任务',
                    '按主力、抗线、翻地、拆要塞分别评价，主力资源先集中前三队',
                    '任务价值与主力对战强度不同，工具队仍可有用途',
                    '把五个队伍表格都理解成五支强主力', [9, 10, 32, 36, 38]),
               rule('开荒配置之后还需要转型且后期核心未齐',
                    '写出转型所需资源与退出时点，再决定觉醒、拆解和装备投入',
                    '短期收益须抵扣永久资源锁定和转型成本',
                    '为临时队耗掉后期主队必须的材料和单份战法', [11, 39, 40])],
        resources=['前三主力资源完整性', '工具队使用频率与转型材料'],
        limits=['主力顺序属于示例账号', '功能队的抗线收益仍需实战'],
        excluded=['第四、第五队与前三队等强', '旧高红武将必然值得再建主力'],
        check='protection', refs=[23, 24, 38],
        questions=['第四、第五队具体承担什么任务？过渡队何时拆、投入哪些不可回收材料？'],
        related=['007', '042', '045']),
    '007': dict(tags=['减队', '机会成本', '任务保留'],
        rules=[rule('第三队占核心资源而实际战损、出勤或成绩不佳',
                    '模拟资源回流到前两队的净收益，净收益为正才缩为两队',
                    '比较对象是全账号收益，而非队伍数量',
                    '无战报就断言两队一定胜过三队，或只因有三名将就维持第三队', [9, 17, 23, 30, 31, 32, 38]),
               rule('待拆队承担其他队不能替代的专门任务',
                    '先评估其任务价值与最低保留成本，再决定释放哪些资源',
                    '翻地、攻城、抗线的不可替代价值不能只用伤害排名衡量',
                    '拆掉关键功能队，却只计主力增益不计任务损失', [10, 26, 32])],
        resources=['被回收战法与觉醒投入', '三队出勤、损耗、资源回流收益'],
        limits=['历史白板魏智表现不等于当前账号', '两队或三队数量没有统一答案'],
        excluded=['两队永远优于三队', '工具队一定应拆'],
        check='rare_counts', refs=[20, 31],
        questions=['第三队有何事件战报与出勤数据？回收各战法后哪条失效链能补齐？'],
        related=['006', '045', '057']),
    '008': dict(tags=['付费方案诊断', '攻击事件', '原方案重复占用'],
        rules=[rule('原付费方案逐队看来有配置，但曹彰缺前期行动保护、甘宁触发不足',
                    '检查主输出的行动通道与事件频率，再分配战必、计险或增益',
                    '价格与高品质战法不能证明全局链条成立',
                    '付费即权威，或把一次纠错推广为所有同名英雄必须携带相同战法', [9, 10, 11, 35, 39, 40]),
               rule('原第二、第三队同时放入攻其不备',
                    '先核本次总份数；单份时记为原方案不可共存，再检查修正方案',
                    '这是被点评配置的资源问题，不应混淆为作者修正方案错误',
                    '把原表当正式可执行方案，或默认所有战法都只有一份', [23, 27, 35, 38])],
        resources=['攻其不备、战必、计险的总份数', '曹彰行动保护和甘宁有效触发次数'],
        limits=['计险获取阶段为本地暂定征服', '示例战法数须回到实际账号'],
        excluded=['付费方案可靠性由价格保证', '及锋对所有甘宁体系都必需'],
        check='duplicate_gongqi', refs=[23, 27, 38],
        questions=['攻其账号右值几份？原方案是否要保留？曹彰早期行动被什么事件打断？'],
        related=['013', '057', '061']),
    '009': dict(tags=['低投入', '核心覆盖', '持有与获取'],
        rules=[rule('低投入账号比较曹操、孙权、刘备的价值',
                    '比较现有配套、缺口、替代成本和真实可组成的队伍覆盖',
                    '核心适配性是账号条件函数，泛用模板数量并非当前收益',
                    '把历史价值排序写成通用三皇强弱排名', [9, 10, 30, 31, 33]),
               rule('同一核心可出现在多个候选队壳',
                    '候选覆盖与同时上队数量分开统计，并查共享战法',
                    '一名核心不能同时复制到多个队伍',
                    '用模板数量夸大账号可同时运作的主力数', [17, 21, 25, 32])],
        resources=['现有核心及真实配套', '稀缺战法、宝物和红度门槛'],
        limits=['约90%拥有木鹿没有样本证据', '版本及低红依赖只能在指定体系讨论'],
        excluded=['90%玩家持有木鹿的统计事实', '曹操固定第一或低投入孙权、刘备没有价值'],
        check='functional_substitute', refs=[21, 25, 31],
        questions=['已有哪一版本核心？补齐哪队成本最低？候选队壳共享哪些将法？'],
        related=['056', '042', '005']),
    '013': dict(tags=['先识别核心', '控制通道', '木鹿边界'],
        rules=[rule('吕布、曹纯、曹操看似核弹壳，但实际缺曹彰式爆发出口',
                    '先识别获胜机制，再按触发频率、行动顺序和保护重组',
                    '同阵营、同位置替换不保证输出链等价',
                    '把队名或同位置直接当体系成立证据', [9, 20, 38, 39]),
               rule('魏智遭普攻爆头，同时考虑木鹿替换',
                    '把反计与普攻保护分开；木鹿被动策略伤害保留不等于所有输出免怯战',
                    '战必阻断普攻，反计针对主动；木鹿的分兵与每回合被动策略攻击须分拆',
                    '宣称木鹿完全不怕战必，或用封主动替代普攻保护', [10, 11, 27, 31, 40])],
        resources=['反计、一夫的跨队占用', '输出频率、距离和控解顺序'],
        limits=['木鹿自带描述本地有拼接重复', '普通/SP姜维仍按精确版本核查'],
        excluded=['木鹿所有攻击都免疫怯战', '队名与历史纠错证明现代强度'],
        check='mulu_control', refs=[11, 27, 40],
        questions=['魏智第一个致命事件属于普攻、主动还是控制？木鹿损失的是哪部分伤害？'],
        related=['008', '056', '061']),
    '016': dict(tags=['同壳不同质', '缺口重组', '逐效果冲突'],
        rules=[rule('三名武将与参考队相同，但宝物、规避、后期增益或前期保护不同',
                    '逐段核查获胜链，允许集中为三队补齐硬缺口',
                    '相同名单只证明队壳，不证明同样的行动和生存条件',
                    '截图同款就判等强，或为第四队继续稀释关键资源', [9, 10, 30, 38]),
               rule('回流账号早期暂缺某XP战法，想用同类型战法替代',
                    '先核已有与新获取阶段，再按具体功能与相同效果选择替代',
                    '同类型不等于冲突，XP标签也不独自等于赛季开放',
                    '将同类型全部判冲突，或把所有XP一律排除在S赛季', [31, 32])],
        resources=['宝物、前期保护、后期放大及实际库存', '被缩减队伍的占用'],
        limits=['XP新获取阶段不明必须条件化', '无法补齐核心时记录替代损失'],
        excluded=['同三将配置可照抄', 'XP统一按同一开放阶段'],
        check='stage_split', refs=[32],
        questions=['相同队壳缺哪一段？战法已有可用还是准备新获取？'],
        related=['005', '026', '039']),
    '026': dict(tags=['三队完成度', '红度兑现', '兵种替换'],
        rules=[rule('平民账号有高红核心，但只能支撑三条完整获胜链',
                    '三队达到功能闭环即可停建，先兑现高红核心的联动',
                    '队数来自资源支持能力，不是把闲置将填满',
                    '高红就单独开新队，造成全局核心法不足', [9, 10, 30, 31, 38]),
               rule('考虑把何太后换姜维并调整步兵分支',
                    '重查实际兵系、站位、形兵条件与失去的保护功能',
                    '形兵要求三将兵系均不同，换将或转兵会改变整条前提',
                    '把一次具体转兵方案推广为任何同名卡都适用', [11, 22, 23, 32])],
        resources=['高红核心配套', '形兵、攻其等单份战法与转兵条件'],
        limits=['姜维弓步共用自带，不能靠名字锁定', '旧案例三队不是当前固定上限'],
        excluded=['何太后固定弱于姜维', '高红无需检查触发'],
        check='xingbing', refs=[22, 23, 32],
        questions=['替换后实际兵系和前锋保护是什么？红度收益能否进入有效攻击事件？'],
        related=['006', '016', '057']),
    '039': dict(tags=['缺孙权', '功能转型', '速度目标'],
        rules=[rule('账号没有孙权，原队壳依赖解控规避',
                    '允许改用不同获胜结构，先形成主队再分配后队',
                    '同位置替代不能补回孙权的全部机制',
                    '强凑无孙权同款流氓队并声称功能等价', [9, 10, 34, 36]),
               rule('历史方案要求司马炎、魏延、乐进全速度',
                    '先写想达成的行动顺序，再按最终面板、宝物和对手复算',
                    '速度是为了事件先后，不是可跨账号复制的固定加点',
                    '照抄全速度却未获得先手，或损失必要输出', [11, 35])],
        resources=['久战与大赏的跨队调拨', '最终战斗速度与对手行动证据'],
        limits=['久战本地获取阶段暂定征服', '速度结论不得视作当前阈值'],
        excluded=['无孙权的固定最优阵容', '三将永远全速度'],
        check='stage_split', refs=[24, 31, 35],
        questions=['实际缺解控还是规避？目标行动顺序怎样，最终面板能否实现？'],
        related=['056', '016', '060']),
    '042': dict(tags=['缺将止损', '负面案例', '第四队成本'],
        rules=[rule('战法充足但缺核心将，第四队只能勉强拼起',
                    '先保三支成熟队，第四队写为低优先级待证，不因有五星而建',
                    '战法库存不能制造不存在的核心功能',
                    '把原文不推荐的四不像队当正常推荐模板', [9, 10, 30, 31, 32, 35]),
               rule('准备给低优先级第四队追加征兵、宝物与时间',
                    '比较补齐成本和前三队被削弱程度，未见收益先止损',
                    '投入还包含出勤和养成，不能只算战法名称',
                    '把能上阵当值得投入，忽略完整队机会成本', [11, 34, 36, 42])],
        resources=['缺失核心将', '前三队占用、觉醒、征兵、宝物与时间'],
        limits=['没有第四队足量事件战报', '原文负面定位必须随队伍配置一起保留'],
        excluded=['第四队是正式推荐', '战法多就能组成同等数量主力'],
        check='rare_counts', refs=[27, 31, 36],
        questions=['第四队要补哪名不可替代核心？它有什么任务与实战收益？'],
        related=['005', '006', '007']),
    '045': dict(tags=['单份分配', '过渡期限', '任务评价'],
        rules=[rule('浑水、反计仅一份，三队职责不同',
                    '按缺失后损失和替代成本分配，评价控制恢复窗口而非只排伤害',
                    '资源顺序来自当时边际收益，不等于永久强度排名',
                    '把所有队伍都补同一满配，或用总伤害否定任务队', [8, 9, 11, 20, 26, 30, 31]),
               rule('马岱、马谡、张绣承担开荒过渡职责',
                    '写退出时点并控制觉醒、XP和永久战法投入',
                    '短期队有期限，过度投入可能阻塞之后主力',
                    '没有退出路径就为过渡队追加不可回收成本', [10, 23, 29])],
        resources=['浑水、反计总份数', '过渡队材料与后续主队资源'],
        limits=['本文马岱具体版本不得仅按姓名外推', '资源先后与账号目标有关'],
        excluded=['固定三队强度排序', '开荒队应永久保留满投入'],
        check='transition_identity', refs=[8, 10, 23],
        questions=['马岱具体自带与ID是什么？过渡结束何时，反计移给哪队收益最大？'],
        related=['006', '055', '067']),
    '055': dict(tags=['缺将缺法', '逐队扣账', '卡法标识分离'],
        rules=[rule('缺乐进、张机、垒实、张绣，第一队需先过渡',
                    '先找可平滑转型且功能完整的第一队，再从余量续配',
                    '补核心顺序与后队可用资源相互依赖',
                    '每队都拿同一池满配，或用缺核心的壳当成熟队', [9, 20, 34, 35]),
               rule('马岱、马谡战法图标带XP/S2等来源标签',
                    '使用奉令护蜀、心战为上与卡本体证据核版本，来源标签另存',
                    '英雄标签和学习战法来源属于不同字段',
                    '因为图标来源而给武将冠XP/S2版本，或原帧退役后猜标识', [10, 18, 19, 36])],
        resources=['首队到后队连续扣减', '张绣等缺失核心的替代成本'],
        limits=['卡面源材料已退役，未明确标识不能新增断言', '令无暂定获取阶段须保留'],
        excluded=['每队可脱离剩余库存独立满配', '战法角标证明英雄XP'],
        check='transition_identity', refs=[10, 18, 19, 36],
        questions=['第一队未来转型所需将法何时齐？武将具体ID与标识有本次证据吗？'],
        related=['001', '045', '060']),
    '056': dict(tags=['功能替代', '不完全等价', '后队上限'],
        rules=[rule('缺曹彰、张机、孙权等核心，需要华雄、甄洛、貂蝉替代',
                    '把输出、恢复、减伤、解控、规避分别列出，写明补回与失去的功能',
                    '同一功能位替代仅能覆盖部分能力，不能承诺全部等价',
                    '甄洛替张机就当恢复加减伤齐全，貂蝉替孙权就当获得群体解控', [9, 34, 35]),
               rule('法刀先占神兵、大赏、反计，之后仍需要魏智或甘宁队',
                    '按剩余资源重验后队的前期保护、触发与生存窗口',
                    '后队上限受第一队分配制约，替代并非零成本',
                    '把四套并存案例拆为四套各自完整的标准模板', [10, 19, 27, 31, 36])],
        resources=['单份神赏反计', '缺失核心的具体功能与合法替代'],
        limits=['貂蝉不补孙权群体移除有害效果', '本地闭月描述含拼接回合数'],
        excluded=['功能位替代即机制等价', '残余资源队有满配强度'],
        check='functional_substitute', refs=[9, 34, 35],
        questions=['替换失去解控、减伤还是恢复？哪些对手会首先击穿该缺口？'],
        related=['009', '013', '039']),
    '057': dict(tags=['账号级最优', '任务覆盖', '事件反馈'],
        rules=[rule('用户指定队数，但将法不足以每队完成输出与保护',
                    '先按实际任务与资源保证主力闭环，再安排碰瓷、练级、攻城',
                    '减少不完整投入可让多支核心跨过可用门槛',
                    '把固定两队或三队当政策，或为了凑数留下硬缺口', [8, 9, 32, 39, 41, 45]),
               rule('方案自称没有盲点，或依据一场胜负想大改',
                    '用常见威胁与队伍职责建立覆盖矩阵，再找重复失效事件',
                    '覆盖比较是结构推断，最优与无敌需要更多证据',
                    '模板多就声称覆盖全环境，单场随机失败就换整套', [11, 34, 35, 36, 42, 43, 47])],
        resources=['英雄及战法唯一占用', '任务、出勤、材料、宝物和当前对手'],
        limits=['未知账号资产必须显式保留未知', '覆盖矩阵不证明无敌或数学最优'],
        excluded=['结构通过保证强度', '队伍数越多克制面越全'],
        check='account_count_rule', refs=[22, 23, 38, 40],
        questions=['用户保留哪些旧队？已分配法是否允许回收？威胁矩阵与事件战报是否齐全？'],
        related=['007', '042', '061']),
    '060': dict(tags=['三队连续决策', '残缺体系成本', '主动辅助'],
        rules=[rule('第一队占用神赏反计，第二队只能另找保护',
                    '以夏侯惇、百战、一夫作为保护候选，再用对手事件链检验缺反计的损失',
                    '这是特定余量下的承伤思路，不是反计的全机制等价替换',
                    '拆开照抄三队，或声称承伤代替主动压制后没有代价', [9, 11, 23, 24, 31, 32]),
               rule('只有半套体系，另一候选有XP田丰辅助主动',
                    '先比较补齐成本，并检查田丰行动、主动目标与下次行动增益',
                    '尽言直谏不是无条件全队常驻提高所有战法发动率',
                    '已有一核心就强凑原体系，或忽略辅助先后手和所选战法', [10, 27, 28, 30, 32])],
        resources=['神赏反计先行占用', '田丰辅助目标、主动战法及保护窗'],
        limits=['具体前两回合爆发不等于神赏仅持续两回合', 'XP田丰版本按卡ID锁定'],
        excluded=['三队可分别照抄为满配', '田丰无条件提升全部主动'],
        check='tianfeng', refs=[27, 28, 32],
        questions=['第三队各主动何时行动？田丰随机选中谁，首个增益何时兑现？'],
        related=['001', '055', '056']),
    '061': dict(tags=['复合效果', '触发与资源', '始计目标待复核'],
        rules=[rule('不攻与久战同队或始计与其他增伤同队',
                    '逐效果比类别、实际目标、有效时间与施加顺序，保留不冲突的副效果',
                    '同类同效果冲突不能推出整张复合战法失效',
                    '只按名称或指挥类别全部否决，或把日志单效果失效当整法失效', [9, 10, 17, 29, 30, 35]),
               rule('王异追击队考虑攻其，或防守队已缺稳定输出出口',
                    '统计有效物理攻击事件与覆盖目标；分别比较输出补齐和跨队替换成本',
                    '攻其由攻击伤害事件叠层，叠防守不必然建立获胜链',
                    '高品质法直接覆盖，或只加保护掩盖无伤害出口', [8, 11, 20, 23, 26, 31, 32, 36])],
        resources=['攻其单份与跨队替换', '四回合事件顺序和稳定输出'],
        limits=['P010写携带者下一次，与本地始计文本我军大营下一次不一致', '不攻与久战实际冲突仍需目标、时点和战报'],
        excluded=['始计给携带者下一次攻击增伤', '同类即整法全部失效'],
        check='shiji_conflict', refs=[9, 10, 29, 35],
        questions=['始计目标文本是否已在当前客户端确认？久战与不攻实际覆盖谁、先施加哪项？'],
        related=['008', '013', '057'])
}


def main():
    manifest = read_json(OUT / '阅读清单.json')
    metadata = {r['no']: r for r in manifest['records']}
    expected = {f'{n:03}' for n in manifest['group_assignments'][GROUP]}
    assert set(SPECS) == expected
    skills = read_json(ROOT / '资料库/official_skill_db.json')['skills']
    extras = read_json(ROOT / '资料库/skill_extra.json')
    heroes = read_json(ROOT / '资料库/hero_extra.json')
    exact = {r['hero_id']: r for r in read_json(ROOT / '资料库/hero.json')}
    source_paths = ['资料库/official_skill_db.json', '资料库/skill_extra.json',
                    '资料库/hero_extra.json', '资料库/hero.json',
                    '.workbuddy/memory/RULES/02_实体核验.md',
                    '.workbuddy/memory/RULES/04_数据源.md',
                    '资料库/官方机制库/基础机制判断规则_20260901.md',
                    '资料库/官方机制库/战法冲突判定规则_20260901.md']
    selected_skills = ['神兵天降', '大赏三军', '反计之策', '攻其不备', '战必断金',
                       '计险远近', '令无空悬', '及锋而试', '磐阵善守', '形兵之极',
                       '夔吼象踏', '九锡黄龙', '洛水佳人', '金匮要略', '闭月',
                       '列营守险', '方阵掩杀', '尽言直谏', '不攻', '久战熟谋', '始计']
    evidence = {
        'verified_date': '2026-10-12', 'verification_scope': 'Saved local files only; not current online data',
        'source_hashes': {rel: digest(ROOT / rel) for rel in source_paths},
        'skills': {name: {'saved_description': skills[name],
                          'copy_rows': [{k: r.get(k) for k in ['id', 'name', 'skillCount', 'notice']}
                                        for r in extras if r['id'] == skills[name]['id']]}
                   for name in selected_skills},
        'heroes': []}
    for r in heroes:
        if r['name'] in ['姜维', '太史慈', '孙权', '木鹿大王', '马岱', '马谡']:
            x = {k: r.get(k) for k in ['id', 'name', 'uniqueName', 'methodId', 'methodName',
                                      'country', 'type', 'distance']}
            h = exact.get(r['id'], {})
            x['exact_id_builtin_match'] = h.get('skill_init') == r['methodId']
            x['exact_id_star'] = h.get('quality') if x['exact_id_builtin_match'] else None
            evidence['heroes'].append(x)
    (OUT / '01_本地交叉核对证据.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', 'utf-8')

    # Specific comparisons were inspected from these saved files during reading.
    checks = {
      'hero_version': ('姜维能否仅凭列营守险锁SP版本', 'conditional',
          'hero_extra: 102012蜀弓、100074蜀步均methodId=200072列营守险；太史慈102003=200706方阵掩杀，100090=200088方阵突击；精确ID与hero.json自带一致。',
          '姜维必须加卡标识、兵种或初始属性，不能只看自带；现有报告SP记载不据此判假。'),
      'rare_counts': ('稀缺增益和保护必须全账号计份数', 'supported_locally',
          'skill_extra: 神兵200204、大赏200198、反计200220均skillCount=1，notice亦可配置1个武将。',
          '支持单份争用的结构前提；实际账号右值与拥有仍须另验。'),
      'protection': ('战必与反计保护针对同一种行动吗', 'supported_locally',
          '战必200228为前三回合怯战阻止普攻；反计200220降低前三回合主动伤害并首回合犹豫。',
          '不能把普攻保护和主动保护无损互换，工具队定位不因此自动变强。'),
      'duplicate_gongqi': ('原表第二、第三队攻其不备是否可同时分配', 'conditional',
          '攻其200755在skill_extra.skillCount=1，notice可配置1个武将；报告原第二、第三队P023/P027均攻其。',
          '以本地单份上限，原方案不能共存；这是原方案诊断，实际账号份数另验。'),
      'functional_substitute': ('恢复、减伤、解控、控制功能能否全等价替换', 'supported_locally',
          '九锡200030移除全军有害效果并规避；洛水200015概率恢复；金匮200773前三回合减伤与受伤恢复；闭月200005暴走/降防且准备一回合。',
          '甄洛未补张机前期减伤，貂蝉未补孙权解控；闭月文本拼接3/4回合不取确定当前数值。'),
      'mulu_control': ('木鹿不怕战必能否解作完全免疫怯战', 'conditional',
          '夔吼200772含分兵状态和每回合被动策略攻击两部分；战必200228阻止普通攻击；基础规则区分被动策略与普攻、追击通道。',
          '保留被动策略出口不代表普攻、分兵都不受影响；自带描述重复拼接，当前参数需复核。'),
      'stage_split': ('XP标签是否能直接确定战法开放阶段', 'supported_locally',
          '攻其200755=S3 confirmed；形兵200813/磐阵200816=S3 confirmed；令无200280/计险200248/久战200959=征服赛季 provisional_default。',
          '明确阶段与暂定阶段分开；此为保存库，不证明实际账号已有或当前能新获取。'),
      'xingbing': ('换将与转兵后是否仍满足形兵条件', 'conditional',
          '形兵200813本地描述要求出战3名武将兵系均不相同，附大营主动/追击主战法与前锋、中军独立作用；姜维弓步不能仅按自带消歧。',
          '必须检验三名实际兵系和位置，不能凭队名或同名卡认定全效果生效。'),
      'transition_identity': ('马岱、马谡可否按姓名或战法来源角标锁版本', 'supported_locally',
          '马岱100615=奉令护蜀200865，100139=借刀斩叛200642；马谡100799=心战为上200275，ID与hero.json自带一致。',
          '055有自带证据可定位本地候选；045无明确版本不得扩写。学习法角标不补武将标识。'),
      'account_count_rule': ('占用数及重组是否应只看导出空闲值', 'supported_locally',
          'RULES04/05定义左为空闲、右为总数；导出仅左值，总数按skill_extra推定并标来源；明确保留旧队才继续扣占用。',
          '避免0空闲误判未拥有和无谓减队，未知右值不补猜。'),
      'tianfeng': ('田丰提高主动发动率与伤害的作用范围', 'supported_locally',
          '尽言200966: 自身行动时随机友方群体2个主动，下次行动阶段提高发动率与伤害；选中项期间发动，下回合可选3个主动。',
          '检查选中战法、下次行动与田丰先后手，不套全队常驻增益。'),
      'shiji_conflict': ('P010始计是否增益携带者的下一次攻击', 'conflict',
          '始计200687明确自身行动前使我军大营下一次攻击/策略攻击增伤，携带者受伤后得洞察；不攻200622与久战200959同指挥且含策略增伤。',
          'P010目标措辞需复核；学习卡采用大营目标，但不修改报告/母本/原审计等级。')}
    records = []
    for no, spec in SPECS.items():
        m = metadata[no]
        assert digest(ROOT / m['rel']) == m['source_sha256']
        claim, result, ev, impact = checks[spec['check']]
        records.append({
            'no': no, 'title': m['title'], 'rel': m['rel'],
            'source_sha256': m['source_sha256'], 'reading_status': 'full_text_read',
            'paragraph_count': m['paragraph_count'], 'tags': spec['tags'],
            'transferable_rules': spec['rules'], 'resource_dependencies': spec['resources'],
            'version_and_season_limits': spec['limits'], 'non_transferable_claims': spec['excluded'],
            'local_checks': [dict(claim=claim, source='01_本地交叉核对证据.json及所列规则原件',
                                  result=result, evidence=ev, impact=impact,
                                  evidence_paragraphs=spec['refs'])],
            'application_questions': spec['questions'], 'related_report_ids': spec['related']})
    result = dict(group=GROUP, report_ids=sorted(SPECS),
        scope='17份正文及表格全部阅读；仅学习与本地交叉核对，未做实时参数核验或重审升级。',
        records=records,
        cross_report_lessons=[
            '先找缺将、缺法或行动缺口；有战法不等于有核心，有红度不等于有触发。',
            '队伍数来自任务与资源：该集中时减队，不完整但有特殊任务时可最低成本保留。',
            '单份优先分给缺失损失大、替代成本高的链条，后队按剩余库存重新验算。',
            '功能替代逐项写损失；同位置、同阵营、同三将名单都不证明等价。',
            '过渡队必须有退出时点；工具队按任务评价，负面案例不能删掉不推荐标记。',
            '资源右值、具体版本、当前开放阶段、实际事件战报决定能否迁移。'],
        open_questions=[
            '061 P010始计增益目标与保存库不同：真实调用先确认当前文本，报告修改留待母本同步闭环。',
            '夔吼、闭月、列营等保存描述有重复拼接，不据此宣称当前完整参数。',
            '原素材已退役，本文只能学习保存报告，不能重做原视频证据验收。'])
    (OUT / f'{GROUP}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    lines = [f'# {GROUP[3:]}：17份逐篇学习', '', result['scope'], '',
             '证据锚点P为DOCX全部段落顺序编号，包含表格与空段，不是页码。保存库证据见[本地交叉核对](01_本地交叉核对证据.json)。', '']
    for r in records:
        lines += [f"## {r['no']} {r['title']}", '', f"正文[阅读材料](阅读材料/{r['no']}.txt)；来源哈希与结构见[结构化学习卡]({GROUP}.json)。", '']
        for x in r['transferable_rules']:
            ps = '、'.join(f'P{p:03}' for p in x['evidence_paragraphs'])
            lines += [f"- 条件：{x['condition']}。判断：{x['decision']}。理由：{x['reason']}。误用：{x['failure_mode']}。证据：{ps}。"]
        c = r['local_checks'][0]
        lines += ['', f"本地核对（{c['result']}）：{c['evidence']} {c['impact']}",
                  f"资源依赖：{'；'.join(r['resource_dependencies'])}。",
                  f"适用边界：{'；'.join(r['version_and_season_limits'])}。",
                  f"不可迁移：{'；'.join(r['non_transferable_claims'])}。",
                  f"实际应用先问：{'；'.join(r['application_questions'])}",
                  '关联报告：'+'、'.join(f'[{n}](阅读材料/{n}.txt)' for n in r['related_report_ids']), '']
    lines += ['## 跨报告认识', ''] + [f'- {s}' for s in result['cross_report_lessons']]
    lines += ['', '## 待复核', ''] + [f'- {s}' for s in result['open_questions']]
    (OUT / f'{GROUP}.md').write_text('\n'.join(lines) + '\n', 'utf-8')
    print(json.dumps(dict(group=GROUP, reports=len(records), authored_rules=sum(len(r['transferable_rules']) for r in records),
                          chars=sum(metadata[n]['character_count'] for n in SPECS),
                          paragraphs=sum(metadata[n]['nonempty_paragraphs'] for n in SPECS)), ensure_ascii=False))


if __name__ == '__main__':
    main()
