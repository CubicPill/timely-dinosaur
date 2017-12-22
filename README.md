# timely-dinosaur
南方科技大学教务系统自动选课    
理论上适用于所有[湖南强智科技](http://www.qzdatasoft.com/web/)教务系统平台, 修改链接, 适配登录即可 (不支持志愿选课和积分选课)    
使用 Python3 编写, 基于 requests 和 bs4 包, 网络条件良好时批量选课可在五秒钟内全部完成

## 使用帮助
**Windows:** 到 [Latest Release](https://github.com/CubicPill/timely-dinosaur/releases/latest) 下载 pyinstaller 打包好的 .exe 文件, 创建配置文件后即可运行.        
**Mac OS:** 自行 Google "Mac OS 运行python脚本", 懒人请点[Mac OS 运行python脚本](http://lmgtfy.com/?q=Mac+OS+%E8%BF%90%E8%A1%8Cpython%E8%84%9A%E6%9C%AC)        
**Linux:** 你应该知道怎么运行, 不然还是回去用 Windows 吧      

初次使用时请将 ```config_sample.json``` 改名为 ```config.json```, 并修改配置参数    
目前支持批量选课(需事先将课程 id 写入配置文件) 和交互式单项选课.     
Tips: 可在开放选课预览时提前运行程序获取全部课程信息, 以缩短选课时间


## 配置参数
修改 ```config.json```    
```username``` CAS 登录用户名(学号)    
```password``` CAS 登录密码    
```course_id``` 课程 ID     
新版程序可以接受命令行参数, 请使用 -h / --help 查看详细命令    
参数优先级: 命令行 > 配置文件 > 默认值     

## 获取 course_id
打开教务系统选课页面, 鼠标移至课程 "选课" 超链接上, 右键弹出菜单中点击 "复制链接地址", 得到如下内容:    
```javascript:xsxkFun('201620173000048');```    
其中 ```201620173000048``` 即为课程 id, 填入 ```config.json``` 中即可批量选课

