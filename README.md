# 三国志11(pk2.2)内存资料共享/查询工具

韩版三国志11已经开发了一段时间，但由于内存结构与国内版有差异，所以对于韩版内存的研究还处在非常起步的阶段。 

为了方便将来实现属于韩版的内存修改，希望能通过本项目吸引所有对韩版内存开发感兴趣的大佬一起分享、完善韩版的内存资料。  

内存查询工具和资料贡献的方式请看 说明/README.md 

**任何疑问请QQ联系: 2634258179**

***
## 环境配置
1. Python : 
    - 下载 python 3.10.x : <https://www.python.org/downloads/windows/>
    ![download python](https://raw.github.com/pdt012/San11MemoryInfo/main/images/download-python.PNG)
    - Windows下安装 (64-bit) 记得勾选最下面
    ![isntall python](https://raw.github.com/pdt012/San11MemoryInfo/main/images/install-python.PNG)
    - python 环境变量配置  (*如果上一步勾选了add python.exe to PATH 则这步可跳过*) <https://blog.csdn.net/stalbo/article/details/71479767>
2. Git
    - 下载 git : <https://git-scm.com/download/>  一直点下一步就行
3. VSCode (*如果只做资料整理，不做代码开发的话可以不下载*)
    - 下载 vscode : <https://code.visualstudio.com/download>
    - 下载 python tool :  
    ![vsocde python tool](https://raw.github.com/pdt012/San11MemoryInfo/main/images/vscode-python-tool.PNG)

***
## git 

*如果没有该仓库管理员权限，请直接跳到1.2*

### 1.1.1 克隆仓库(管理员)
1. 新建一个存项目的文件夹
2. 右键 git bash here
3. 输入 `git clone https://github.com/pdt012/San11MemoryInfo.git`
### 1.1.2 新建分支(管理员)
1. 主分支是锁定的不允许直接上传，所有操作必须在分支内进行
2. 进入San11MemoryInfo文件夹，右键git bash here
3. 输入 `git checkout -b 你的分支名`
4. 会提示切换到了该分支

### 1.2 克隆仓库(非管理员)
1. 进网页版github :  <https://github.com/pdt012/San11MemoryInfo>
2. 点击fork将项目拷贝到自己的账户
3. 电脑新建一个存项目的文件夹
4. 右键 git bash here
5. 输入`git clone https://github.com/你的用户名/San11MemoryInfo.git`

### 2 资料编辑
1. 进入San11MemoryInfo文件夹修改资料

### 3 上传合并修改
1. 进入San11MemoryInfo文件夹，右键git bash here
2. 输入 `git add .`
3. 输入 `git commit -m "备注修改内容"`
    - 可能会提示输入用户名和邮箱，按提示操作即可
4. (*没有新建过分支则跳到 5*) 输入 `git push origin 你的分支名`
5. (没有新建分支时) 输入 `git push` 即可
    - 会要求输入账号密码，密码不是github密码而需要自己新建一个登录用的token
    - 教程链接 : <https://blog.csdn.net/chengwenyang/article/details/120060010>
6. 如果以上都没有问题，进github仓库，新建pull request，红框处选择自己的分支
![pull-request](https://raw.github.com/pdt012/San11MemoryInfo/main/images/github-pull-request.PNG)
![pull-request-2](https://raw.github.com/pdt012/San11MemoryInfo/main/images/github-pull-request-2.PNG)


