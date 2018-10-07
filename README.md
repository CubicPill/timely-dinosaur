# timely-dinosaur
南方科技大学教务系统自动选课    
理论上适用于所有[湖南强智科技](http://www.qzdatasoft.com/web/)教务系统平台, 修改链接, 适配登录即可 (不支持志愿选课和积分选课)    
使用 Python3 编写, 基于 requests 和 bs4 包, 一般选课请求过程会在 200ms 内完成    
附带一套辅助排课的 Web UI, 可以可视化搜索添加课程并保存课程 ID     

## 使用帮助
暂时不提供打包好的可执行文件, release 中为不含 Web UI 的旧版, 谨慎使用

运行选课主程序:      
```
python3 run.py
```
运行排课辅助:    
```
python3 run.py -w
```

初次使用时请将 ```config_sample.json``` 改名为 ```config.json```, 并修改配置参数    
参考 ```courst_list_sample.txt``` 创建自己的 ```course_list.txt```    
Tips: 可在开放选课预览时提前运行程序获取全部课程信息, 以缩短选课时间


## 配置参数
### 修改 ```config.json```
```username``` CAS 登录用户名(学号)    
```password``` CAS 登录密码    
新版程序可以接受命令行参数, 请使用 -h / --help 查看详细命令
参数优先级: 命令行 > 配置文件 > 默认值     

### 修改 ```course_list.txt```
填入课程编号即可, 每行一个, 可以加井号作注释, 请参考样例 `course_list_sample.txt`    
**注意:** 使用 Web UI 的保存功能时将会覆盖掉原有的 `course_list.txt`    

## 获取 course_id
打开教务系统选课页面, 鼠标移至课程 "选课" 超链接上, 右键弹出菜单中点击 "复制链接地址", 得到如下内容:    
```javascript:xsxkFun('201620173000048');```    
其中 ```201620173000048``` 即为课程 id, 填入 `course_list.txt` 中即可批量选课
