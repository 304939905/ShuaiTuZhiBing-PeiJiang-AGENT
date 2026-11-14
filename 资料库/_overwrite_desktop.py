import shutil, os, traceback
out=[]
try:
    SRC='D:/Desktop/shandou/学习汇报/全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_精编学习报告.docx'
    old='C:/Users/Administrator/Desktop/攻其篇精编学习报告_2026-08-19.docx'
    shutil.copy2(SRC, old)
    out.append('[overwrite old 19] exists=%s size=%d' % (os.path.exists(old), os.path.getsize(old)))
    # 清理临时脚本
    for f in ['_regen_and_check.py','_regen_result.txt','_selfcheck.py','_selfcheck_out.txt','_list_desktop.py','_list_desktop_result.txt','_check_gongqi.py','_check_out.txt','_check_zhenrong.py','_check_zhenrong_result.txt','_check_ctx.py','_check_ctx_result.txt','_check_zr2.py','_check_zr2_out.txt','_check_result.txt']:
        p='D:/Desktop/shandou/资料库/'+f
        if os.path.exists(p):
            os.remove(p)
    out.append('[cleanup temp] done')
except Exception as e:
    out.append('EXC '+traceback.format_exc())
open('D:/Desktop/shandou/资料库/_overwrite_result.txt','w',encoding='utf-8').write('\n'.join(out))
