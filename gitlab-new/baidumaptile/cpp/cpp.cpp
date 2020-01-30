/*
20190821小结：
对于需要运行opencv 4.1.1版本的visual studio 2019 vc++工程，由于2019版本改版了，截止目前还没有找到针对opencv等的global设置项，
现需要在每一个工程里面设置opencv路径。
1、在右侧解决方案资源管理器内右击工程名称 => 属性 => 在对话框上方，选择x64 并且点击“配置管理器”将弹出“配置管理器”对话框
选择“活动解决方案平台”为x64(选择以后下方的“项目上下文”列表中的“平台”应该会自动变成x64)
2、回到“xxx项目属性页”对话框，在左侧选择“C/C++” => 常规 => 在“附加包含目录”输入 $(OPENCV_DIR)\..\..\include
3、在左侧选择“链接器” => 常规 => 在“附加库目录”输入 $(OPENCV_DIR)\lib
4、在左侧选择“链接器” => 输入 => 在“附加依赖项”添加 opencv_world411d.lib
注意，这里如果本工程使用debug版本，添加opencv_world411d.lib；如果是发布版本，需要添加opencv_world411.lib；否则链接时会报错。
5、回到“xxx项目属性页”对话框 => 配置属性 => 高级 => MFC的使用，这个项目里面设置成为：在共享DLL中使用MFC
6、注意如果需要运行opencv_world411d.dll这种依赖包的话，需要将opencv_world411d.dll拷贝到.exe相同目录(xxx\Debug)内；对于64位
Windows系统也可以将这种依赖包放置到C:\Windows\System32文件夹内。c++用GetSystemDirectory 函数和GetWindowsDirectory 函数检索
这些目录。参考：
vs编译成功生成exe后运行时，提醒无法启动程序，计算机中丢失xx.dll：https://bbs.csdn.net/topics/390618968?page=1
VS DLL 复制本地：https://www.cnblogs.com/nzbbody/p/3436130.html

官网文档：https://docs.opencv.org/4.1.1/
https://docs.microsoft.com/en-us/cpp/build/creating-precompiled-header-files?view=vs-2019
stdafx.h到底有什么用？https://blog.csdn.net/follow_blast/article/details/81704460
C++之"stdafx.h"的用法说明：https://blog.csdn.net/fyf18845165207/article/details/82818057

下面这2篇是误导
OpenCV3.4+VisualStudio2017开发环境配置指导：https://jingyan.baidu.com/album/dca1fa6f13bd55f1a44052b9.html?picindex=1
解决C++ MFC源码运行时 由于找不到MFC42D.DLL，无法继续执行代码（可能仅限于mfc内置dll包；而不是像opencv这样的外部依赖包。另外
采用静态库以后，编译的exe文件从200kb变成了12MB）：https://blog.csdn.net/q297896911/article/details/80329692

下面被采纳了：
学习OpenCV--如何在Visual Studio中使用OpenCV：https://www.cnblogs.com/shlll/archive/2018/02/06/8424692.html
“模块计算机类型“x64”与目标计算机类型“X86”冲突解决方案：https://blog.csdn.net/u014805066/article/details/78143091
https://docs.opencv.org/master/dd/d6e/tutorial_windows_visual_studio_opencv.html
上面一篇官网文章说，当使用local method来配置opencv到每一个项目中的时候，
需要添加$(OPENCV_DIR)\..\..\include路径到项目中
Next go to the Linker –> General and under the *"Additional Library Directories"* add the libs directory:
$(OPENCV_DIR)\lib
opencv_(The Name of the module)(The version Number of the library you use)d.lib
上述local method非常麻烦，建议直接使用global method:
Tools –> Options –> Projects and Solutions –> VC++ Directories.
add the include directories by using the environment variable OPENCV_DIR
c++ 出现“ error LNK2019: 无法解析的外部符号 该符号在函数 中被引用"错误原因：https://www.cnblogs.com/bile/p/8116809.html
“error LNK2019: 无法解析的外部符号”的几种可能原因：https://blog.csdn.net/wangchangcheng12306/article/details/80583168
*/
#include "stdafx.h"

using namespace std;

//void test01(void);
//void test02(void);
//void test03(void);
//void test04(void);
//int test05(void);
//int test06(void);

//void test01(void)
//{
//	BasicOperation bo;
//	string folderName = "screen_snapshot";
//	string filePrefix = "heatmap_";
//	int result = bo.ScreenSnapshot(folderName, filePrefix);
//	string folderPath = bo.rootPath + "\\" + folderName + "\\*.*";
//	int fileNumber = bo.GetFileNumberInDirectory(folderPath);
//	cout << folderPath << " has: " << fileNumber << endl;
//}
//
//void test02(void)
//{
//	BasicOperation bo;
//	int result = bo.GetRandomTime(5000, 3000);
//	long long currentTs = bo.GetCurrentTs();
//	cout << result << " seconds; current ts == " << currentTs;
//	string dataToClipboard = "testing";
//	bo.CopyToClipboard(dataToClipboard);
//}
//
//void test03(void)
//{
//	BasicOperation bo;
//	string filePath = bo.rootPath + "//..//inputs//test.txt";
//	bo.ReadFileToAttribute(filePath);
//	cout << bo.clientHeight << "; width ==" << bo.clientWidth << endl << bo.rootPath << endl;
//}

/*
#include <Windows.h>
#include <vector>
*/
//void test04(void)
//{
//	vector<ScreenPoint> pt_vector;
//	//vector<POINT> pt_vector;
//	BasicOperation bo;
//	bo.PrintXY(pt_vector, 3000);
//	string output = bo.ConvertIntToString(pt_vector);
//	string filePath = bo.rootPath + "\\outputs\\out.txt";
//	bool result = bo.WriteFile(output, filePath);
//	cout << result << ": content == " << output << endl;
//}

/*
#include "BasicOperation.h"
*/
//int test05(void)
//{
//	BasicOperation bo;
//	MouseTrace mt = {
//		500, 300, 800, 600, 300, toRight
//	};
//	string errorMsg = bo.CheckMouseTraceStructure(mt);
//	if (0 < errorMsg.length()) {
//		cout << errorMsg << endl;
//		return -1;
//	}
//	bo.DragTheMap(mt);
//	return 0;
//}

/*
测试OpenCV类
*/
int test06(void)
{
	BasicOperation bo;
	InitAttribute initAttr = {
		bo.rootPath,bo.clientWidth,bo.clientHeight,bo.windowWidth,bo.windowHeight
	};
	OpenCV oCV(initAttr);
	/*string imageFilePath = bo.rootPath + "/../../inputs/matches.jpg";
	int result = oCV.ShowImage(imageFilePath);
	cout << bo.rootPath << endl << imageFilePath << endl << "show result == " << result << endl;
	return result;
	*/
	cv::Mat src;
	oCV.ScreenSnapshot(src);
	imshow("src", src);
	cv::waitKey(0);
	cv::destroyAllWindows();
	return 0;
}

/*
本代码用于爬取
*/
int main(int argc, char* argv[])
{
	int sleepTime = 1000;
	int minimalInterval = 200;

	if (1 < argc && -1 < atoi(argv[1])) {
		sleepTime = atoi(argv[1]);
	}
	cout << "sleepTime = " << sleepTime << "; minimalInterval = " << minimalInterval << endl;
	Sleep(sleepTime);
	test06();
	cout << "Press any key to exit ..." << endl;
	return 0;
}
