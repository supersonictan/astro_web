# astro_web

### About Setup
1. sudo yum install git
2. ssh-keygen -t rsa -b 4096 -C "376079374@qq.com"
3. 复制公钥到git：~/.ssh/id_rsa.pub
4. wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
5. bash Miniconda3-latest-Linux-x86_64.sh
6. conda install beautifulsoup4
7. conda install requests
8. 用于rz和sz命令：sudo yum install lrzsz
9. pip install web.py
10. conda install -c conda-forge jieba 用于cpca 地址解析
11. conda install -c conda-forge cpca
12. 更新conda源
    - conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
    - conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/


### Update——2023年10月17日
 - 增加 knowledge_web.ini 文件
 - TODO：
   + [x] 增加 http 抓取结果的 cache
   + [x] 命主星落宫的解析
   + [x] 婚神落宫的解析
   + [x] 初等学业、高等学业解析
   + [x] 增加性格解析（星性合像等）
   + [ ] 老年痴呆：https://www.douban.com/group/topic/82889068/?_i=9963519IUjPhy-
   + [x] 事业运和公司运：https://www.douban.com/group/topic/23078861/?_i=9927213IUjPhy-
   + [x] 星座性格来看适合职业工作：https://www.douban.com/group/topic/23078665/?_i=9929715IUjPhy-
   + [ ] 看出国：https://www.douban.com/note/170662448/?_i=9929102IUjPhy-
   + [ ] 艺术家金海相位：https://www.douban.com/note/335108891/?_i=9929021IUjPhy-
   + [ ] 元素统计：如何看元素在新盘中的占比？我个人是10大行星+上升+天顶，其中日月升比重给高点，三王星天海冥的比重给低点，其他星分值一样。
   - [] https://www.douban.com/note/100808334/?_i=0536424IUjPhy-,0564900IUjPhy-
   - https://www.douban.com/note/279230945/?_i=0537065IUjPhy-,0559106IUjPhy-
   - https://www.douban.com/note/138619254/?_i=0537022IUjPhy-,0558871IUjPhy-
   - https://www.douban.com/note/766993630/?_i=0534714IUjPhy-,0564908IUjPhy-
   - https://www.douban.com/note/836608088/?_i=0534275IUjPhy-,0564913IUjPhy-
   - 日返：https://www.douban.com/note/607166437/?_i=0533654IUjPhy-,0565528IUjPhy-
   - https://www.douban.com/note/745098309/?_i=0214736IUjPhy-,0565530IUjPhy-
   - https://www.douban.com/note/809544001/?_i=0214739IUjPhy-,0565531IUjPhy-
   - https://www.douban.com/note/717169638/?_i=0537014IUjPhy-,0565555IUjPhy-
   - 日返、月返推运
     - [ ] 工作：跳槽、升职加薪
     - [ ] 财富：财运起伏
       - 健康：健康如何，不好时候说明疾病
       - 恋爱：开始一段恋情、分手、吵架
       - 婚姻：离婚、结婚、吵架
       - 出国旅游：
       - 
   - 根据生日+重大事件做生时校准
