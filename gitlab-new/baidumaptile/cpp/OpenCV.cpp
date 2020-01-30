#include "OpenCV.h"

using namespace cv;
using namespace std;

/*
Default constructor

References:
《C++ Primer Plus第6版中文版》Page 356-359
微软VS2019官方文档：https://visualstudio.microsoft.com/vs/getting-started/
https://docs.microsoft.com/en-us/visualstudio/get-started/visual-studio-ide?view=vs-2019
https://docs.microsoft.com/en-us/cpp/mfc/reference/cwnd-class?view=vs-2019
*/
OpenCV::OpenCV(const InitAttribute& initAttributes)
{
	this->InitializeAttributes(initAttributes);
}

/*
Deconstructor
*/
OpenCV::~OpenCV()
{
	//do nothing here
}

/*
pass all these auguments during class initialization
InitAttribute is defined in OpenCV.h
*/
void OpenCV::InitializeAttributes(const InitAttribute& initAttributes)
{
	clientWidth = initAttributes.clientWidth;
	clientHeight = initAttributes.clientHeight;
	windowWidth = initAttributes.windowWidth;
	windowHeight = initAttributes.windowHeight;
	rootPath = initAttributes.rootPath;
}

/*
显示一张图片
*/
int OpenCV::ShowImage(std::string& imageFilePath)
{
	Mat image;
	image = imread(imageFilePath, IMREAD_COLOR); // Read the file
	if (image.empty()) // Check for invalid input
	{
		cout << "Could not open or find the image" << std::endl;
		return -1;
	}
	namedWindow("Display window", WINDOW_AUTOSIZE); // Create a window for display.
	imshow("Display window", image); // Show our image inside it.
	waitKey(0); // Wait for a keystroke in the window
	destroyAllWindows();
	return 0;
}

/*
windows平台利用opencv寻找桌面上的图像：https://blog.csdn.net/qq_18984151/article/details/79689732
*/

/*
抓取当前屏幕函数
References:
作者：windows api+opencv实现动态截屏并显示：https://blog.csdn.net/qq_18984151/article/details/79231953
cv::Mat初识和它的六种创建方法：https://blog.csdn.net/u012058778/article/details/90764430
使用gdi和opencv截屏，并保存。https://blog.csdn.net/jia_zhengshen/article/details/9384245
上面最后一篇博文已经不合适opencv4.1.1版本了而且需要：
#include <opencv2\imgproc\imgproc_c.h>
#include <opencv2\imgcodecs.hpp>

CreateDCA function：https://docs.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-createdca

*/
void OpenCV::ScreenSnapshot(cv::Mat& src)
{
	HBITMAP	hBmp;
	HBITMAP	hOld;
	Mat v_mat;
	BITMAP bmp;
	int nWidth, nHeight, nChannels;

	//创建画板
	HDC hScreen = CreateDC(TEXT("DISPLAY"), NULL, NULL, NULL);
	HDC	hCompDC = CreateCompatibleDC(hScreen);
	//取屏幕宽度和高度
	nWidth = GetSystemMetrics(SM_CXSCREEN);
	nHeight = GetSystemMetrics(SM_CYSCREEN);
	/*int nWidth = clientWidth;
	int nHeight = clientHeight;*/
	cout << nWidth << "; nHeight == " << nHeight << endl;
	//创建Bitmap对象
	hBmp = CreateCompatibleBitmap(hScreen, nWidth, nHeight);
	hOld = (HBITMAP)SelectObject(hCompDC, hBmp);
	BitBlt(hCompDC, 0, 0, nWidth, nHeight, hScreen, 0, 0, SRCCOPY);
	SelectObject(hCompDC, hOld);
	//释放对象
	DeleteDC(hScreen);
	DeleteDC(hCompDC);

	//BITMAP操作
	GetObject(hBmp, sizeof(BITMAP), &bmp);
	nChannels = bmp.bmBitsPixel == 1 ? 1 : bmp.bmBitsPixel / 8;
	//int depth = bmp.bmBitsPixel == 1 ? IPL_DEPTH_1U : IPL_DEPTH_8U; // 需要#include <opencv2/core/core_c.h>

	//mat操作
	v_mat.create(bmp.bmHeight, bmp.bmWidth, CV_MAKETYPE(CV_8U, nChannels));
	GetBitmapBits(hBmp, bmp.bmHeight * bmp.bmWidth * nChannels, v_mat.data);
	
	src = v_mat;
	DeleteObject(hBmp);
}
