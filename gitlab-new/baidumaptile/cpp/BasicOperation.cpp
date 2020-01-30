#include "BasicOperation.h"

// 包括了<Windows.h>；本行不能够放置在"BasicOperation.h"里面，报错
#ifndef AFXWIN_H_
#define AFXWIN_H_
#include <afxwin.h>
#endif

using namespace std;

/*
Default constructor

References:
《C++ Primer Plus第6版中文版》Page 356-359
微软VS2019官方文档：https://visualstudio.microsoft.com/vs/getting-started/
https://docs.microsoft.com/en-us/visualstudio/get-started/visual-studio-ide?view=vs-2019
https://docs.microsoft.com/en-us/cpp/mfc/reference/cwnd-class?view=vs-2019
*/
BasicOperation::BasicOperation()
{
	rootPath = this->GetCwd();
	this->InitializeAttributes(rootPath);
}

/*
A second constructor
*/
BasicOperation::BasicOperation(const std::string& rootPathRef)
{

	this->InitializeAttributes(rootPathRef);
}

/*
Deconstructor
*/
BasicOperation::~BasicOperation()
{
	//do nothing here
}

/*
References:
C++获取屏幕分辨率（屏幕窗口大小），屏幕显示比例（DPI）几种方法：https://blog.csdn.net/yp18792574062/article/details/88351342
*/
void BasicOperation::InitializeAttributes(const std::string& rootPathRef)
{
	/* Initialize screen size */
	HWND hd = GetDesktopWindow();
	RECT rect;
	GetClientRect(hd, &rect);
	if (0 < (rect.right - rect.left) && 0 < (rect.bottom - rect.top))
	{
		clientWidth = (rect.right - rect.left);
		clientHeight = (rect.bottom - rect.top); // 1920,1080
	}

	GetWindowRect(hd, &rect);
	if (0 < (rect.right - rect.left) && 0 < (rect.bottom - rect.top))
	{
		windowWidth = (rect.right - rect.left);
		windowHeight = (rect.bottom - rect.top); // 1920,1080
	}

	/* Initialize rootPath */
	rootPath = rootPathRef;
}

/*
References:
CString和string相互转换：https://blog.csdn.net/u014801811/article/details/90439888
mfc中，如何将CString 转换成 string：https://zhidao.baidu.com/question/79250977.html

#include <afxwin.h>
*/
std::string BasicOperation::GetCwd(void)
{
	CString path;
	GetModuleFileName(NULL, path.GetBufferSetLength(MAX_PATH + 1), MAX_PATH);
	path.ReleaseBuffer();
	int pos = path.ReverseFind('\\');
	path = path.Left(pos);
	std::string pathString(CW2A(path.GetString()));
	return pathString;

	/*TCHAR szDrive[_MAX_DRIVE] = { 0 };
	TCHAR szDir[_MAX_DIR] = { 0 };
	TCHAR szFname[_MAX_FNAME] = { 0 };
	TCHAR szExt[_MAX_EXT] = { 0 };
	_wsplitpath_s(path.GetString(), szDrive, szDir, szFname, szExt);*/
}

/*
References:
C++实现屏幕截图（全屏截图）：https://blog.csdn.net/sunflover454/article/details/48717731
【VC报错】fatal error C1189: #error : WINDOWS.H already included. MFC apps must not #include：https://blog.csdn.net/ypist/article/details/8505666
上文结论：将#include "windows.h"的这一行放在其他#include头文件之后
CWND和HWND之间的关系和转换 和获取方法：https://blog.csdn.net/Alexander_Frank/article/details/52093955
C++string类常用函数 c++中的string常用函数用法总结：https://blog.csdn.net/pengnanzheng/article/details/80549445

#include <afxwin.h>
这个方法放置到OpenCV类里面了。
*/
/*
int BasicOperation::ScreenSnapshot(const std::string& folderNameRef, const std::string& filePrefix)
{
	CWnd* pDesktop;
	HWND Handle = GetDesktopWindow();
	pDesktop = CWnd::FromHandle(Handle);
	CDC* pdeskdc = pDesktop->GetDC();
	CRect re;
	////获取窗口的大小
	pDesktop->GetClientRect(&re);
	CBitmap bmp;
	bmp.CreateCompatibleBitmap(pdeskdc, re.Width(), re.Height());
	//创建一个兼容的内存画板
	CDC memorydc;
	memorydc.CreateCompatibleDC(pdeskdc);
	//选中画笔
	CBitmap* pold = memorydc.SelectObject(&bmp);
	//绘制图像
	memorydc.BitBlt(0, 0, re.Width(), re.Height(), pdeskdc, 0, 0, SRCCOPY);

	//选中原来的画笔
	memorydc.SelectObject(pold);
	BITMAP bit;
	bmp.GetBitmap(&bit);
	//定义 图像大小（单位：byte）
	DWORD size = bit.bmWidthBytes * bit.bmHeight;
	LPSTR lpdata = (LPSTR)GlobalAlloc(GPTR, size);

	//后面是创建一个bmp文件的必须文件头
	BITMAPINFOHEADER pbitinfo;
	pbitinfo.biBitCount = 24;
	pbitinfo.biClrImportant = 0;
	pbitinfo.biCompression = BI_RGB;
	pbitinfo.biHeight = bit.bmHeight;
	pbitinfo.biPlanes = 1;
	pbitinfo.biSize = sizeof(BITMAPINFOHEADER);
	pbitinfo.biSizeImage = size;
	pbitinfo.biWidth = bit.bmWidth;
	pbitinfo.biXPelsPerMeter = 0;
	pbitinfo.biYPelsPerMeter = 0;
	GetDIBits(pdeskdc->m_hDC, bmp, 0, pbitinfo.biHeight, lpdata, (BITMAPINFO*)& pbitinfo, DIB_RGB_COLORS);
	BITMAPFILEHEADER bfh;
	bfh.bfReserved1 = bfh.bfReserved2 = 0;
	bfh.bfType = ((WORD)('M' << 8) | 'B');
	bfh.bfSize = size + 54;
	bfh.bfOffBits = 54;
	//写入文件
	CFile file;
	string folder_path(rootPath + "\\");
	if (0 < folderNameRef.length())
	{
		folder_path = rootPath + "\\" + folderNameRef + "\\";
	}
	CString strFileName(folder_path.c_str());
	CreateDirectory((LPCTSTR)strFileName, NULL);
	CTime t = CTime::GetCurrentTime();
	CString tt = t.Format("%Y%m%d_%H%M%S");
	if (0 < filePrefix.length())
	{
		CString prefix(filePrefix.c_str());
		tt = prefix + tt;
	}
	strFileName += tt;
	strFileName += _T(".bmp");
	if (file.Open((LPCTSTR)strFileName, CFile::modeCreate | CFile::modeWrite))
	{
		file.Write(&bfh, sizeof(BITMAPFILEHEADER));
		file.Write(&pbitinfo, sizeof(BITMAPINFOHEADER));
		file.Write(lpdata, size);
		file.Close();
	}
	GlobalFree(lpdata);
	return 0;
}
*/

/*
C / C++遍历目录下的所有文件（Windows篇，超详细）https://www.cnblogs.com/collectionne/p/6792301.html
利用FindFirstFile(),FindNextFile()函数历遍指定目录的所有文件：https://blog.csdn.net/u012005313/article/details/46490437

#include <Windows.h>

调用方法：
BasicOperation bo;
string folderPath = bo.rootPath + "\\screen_snapshot\\*.*";
int fileNumber = bo.GetFileNumberInDirectory(folderPath);
*/
int BasicOperation::GetFileNumberInDirectory(const std::string& folderPath)
{
	int counter = 0;
	int dirs = 0;
	using namespace std;
	HANDLE hFind;
	WIN32_FIND_DATA findData;
	//LARGE_INTEGER size;

	CString dirName(folderPath.c_str());
	hFind = FindFirstFile((LPCTSTR)dirName, &findData);
	if (hFind == INVALID_HANDLE_VALUE)
	{
		return -1;
	}
	do
	{
		if (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)
		{
			//cout << findData.cFileName << "\t<dir>\n";    // 是否是目录 
			dirs++;  // 忽略"."和".."两个结果 
		}
		else
		{
			counter++;
			/*size.LowPart = findData.nFileSizeLow;
			size.HighPart = findData.nFileSizeHigh;
			cout << findData.cFileName << "\t" << size.QuadPart << " bytes\n";*/
		}
	} while (FindNextFile(hFind, &findData));
	return counter;
}

/*
调用方法：
BasicOperation bo;
int result = bo.GetRandomTime(5000, 3000);
*/
int BasicOperation::GetRandomTime(int midtime, int range)
{
	unsigned int timeSeed = time(0) % 100;
	srand(timeSeed);
	if (1 > midtime)
	{
		midtime = RANDOM_MIDTIME;
	}
	if (1 > range)
	{
		range = RANDOM_TIME_RANGE;
	}
	if (range > midtime)
	{
		midtime = range;
	}
	return midtime - range / 2 + rand() % range;
	// rand() returns an int from 0 to RAND_MAX(2147483647)
}

/*
在minimal_int和maximal_int之间获得随机值
调用方法：
BasicOperation bo;
int result = bo.GetRandomInt(500, 800);
*/
int BasicOperation::GetRandomInt(int minimal_int, int maximal_int)
{
	unsigned int timeSeed = time(0) % 100;
	srand(timeSeed);
	if (maximal_int < minimal_int) {
		return maximal_int + rand() % (minimal_int - maximal_int);
	}
	else if (minimal_int == maximal_int) {
		return maximal_int;
	}
	return minimal_int + rand() % (maximal_int - minimal_int);
	// rand() returns an int from 0 to RAND_MAX(2147483647)
}

/*
#include <sys/timeb.h>
References:
c++ 时间类型详解 time_t：https://www.runoob.com/w3cnote/cpp-time_t.html
VC/c++版本获取现行时间戳精确到毫秒：https://www.cnblogs.com/guolongzheng/p/9399414.html
*/
long long BasicOperation::GetCurrentTs(void)
{
	timeb t;
	ftime(&t);
	return t.time * 1000 + t.millitm;
}

/*
References:
C++怎么读写windows剪贴板的内容?比如说自动把一个字符串复制：https://zhidao.baidu.com/question/647698977954822045.html
C++中strcpy()函数和strcpy_s()函数的使用及注意事项：https://blog.csdn.net/leowinbow/article/details/82380252
*/
bool BasicOperation::CopyToClipboard(std::string dataToClipboard)
{
	if (OpenClipboard(NULL))
	{
		EmptyClipboard();
		HGLOBAL clipbuffer;
		char* buffer;
		const char* pszData; // 不能够直接初始化；只能够使用下面这一行代码来赋值
		pszData = dataToClipboard.c_str();
		clipbuffer = GlobalAlloc(GMEM_DDESHARE, dataToClipboard.length() + 1);
		if (0 == clipbuffer) {
			return false;
		}
		buffer = (char*)GlobalLock(clipbuffer);
		if (0 == buffer) {
			return false;
		}
		strcpy_s(buffer, strlen(pszData) + 1, pszData); // strcpy(buffer, pszData);
		GlobalUnlock(clipbuffer);
		SetClipboardData(CF_TEXT, clipbuffer);
		CloseClipboard();
		return true;
	}
	return false;
}

/*
调用方法：
CtrlPaste(300, 500);
#include <Windows.h>：本例子的#include <Windows.h>已经被包括在#include <afxwin.h>里面了。
*/
void BasicOperation::CtrlPaste(int x, int y)
{
	mouse_event(MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE, x * 65535 / clientWidth, y * 65535 / clientHeight, 0, 0);
	Sleep(15);
	mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0);
	Sleep(5);
	mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
	Sleep(10);

	keybd_event(0x11, 0, 0, 0); // CTRL key
	keybd_event(0x41, 0, 0, 0); // A key
	keybd_event(0x41, 0, 2, 0);
	keybd_event(0x11, 0, 2, 0);
	Sleep(10);

	keybd_event(0x2E, 0, 0, 0); // DEL key
	keybd_event(0x2E, 0, 2, 0);
	Sleep(20);

	keybd_event(0x11, 0, 0, 0); // CTRL key
	keybd_event(0x56, 0, 0, 0); // V key
	keybd_event(0x56, 0, 2, 0);
	keybd_event(0x11, 0, 2, 0);
	Sleep(20);

	keybd_event(0x23, 0, 0, 0); // END key
	keybd_event(0x23, 0, 2, 0);
	Sleep(20);

	keybd_event(0x0D, 0, 0, 0); // Enter Key
	keybd_event(0x0D, 0, 2, 0);
}

/*
调用方法：
BasicOperation bo;
string filePath = bo.rootPath + "//..//inputs//test.txt";
bo.ReadFileToAttribute(filePath);
*/
void BasicOperation::ReadFileToAttribute(const std::string& filePath)
{
	char buffer[CHAR_ARRAY_SIZE];
	cout << sizeof(buffer);
	string temp;
	fstream out;

	out.open(filePath, ios::in | ios::binary);
	while (!out.eof())
	{
		out.getline(buffer, CHAR_ARRAY_SIZE, '\n');
		temp = buffer;
		if (5 < sizeof(buffer) && 5 < temp.length())
		{
			cout << "This line is: " << temp << endl;
			CopyToClipboard(temp);
			CtrlPaste(300, 500);
		}
	}
	out.close();
}

/*
References:
https://docs.microsoft.com/zh-cn/windows/win32/api/winuser/nf-winuser-getcursorpos
[C++] GetCursorPos函数的使用方法、应用实例：https://blog.csdn.net/baidu_38494049/article/details/82930099
GetCursorPos() 与GetMessagePos()的区别（判断是否在browser内）：https://blog.csdn.net/jiangqin115/article/details/44916351
MFC的坐标转换GetClientRect/GetWindowRect/ClientToScreen/GetCursorPos/ScreenToClient：https://blog.csdn.net/chunyexiyu/article/details/9020151
C++ 中如何用 vector类作为函数的参数：https://blog.csdn.net/hujunyin/article/details/79489522
c++ 如何获取鼠标在桌面上的坐标：https://jingyan.baidu.com/article/b0b63dbf254a3b4a483070b8.html
C++ vector 容器浅析：https://www.runoob.com/w3cnote/cpp-vector-container-analysis.html

#include <Windows.h>：本例子的#include <Windows.h>已经被包括在#include <afxwin.h>里面了。
todo: 将模板定义成为vector<POINT> &pt_vector，总是报错Windows.h被重复included。所以为了加快开发速度，直接使用自定义ScreenPoint模板。
*/
int BasicOperation::PrintXY(vector<ScreenPoint>& pt_vector, int sleepTimeBetweenPoints)
{
	ScreenPoint new_pt;
	POINT point;
	BOOL bReturn;
	int i = 0;

	Sleep(sleepTimeBetweenPoints);
	bReturn = GetCursorPos(&point);
	while (true) {
		if (0 == bReturn)
		{
			cout << "cannot get the cursor point. Please try again for Point # " << i << " : " << endl;
		}
		else {
			cout << "Point # " << i << " : " << point.x << "," << point.y << endl;
			new_pt = {
				point.x,point.y
			};
			pt_vector.push_back(new_pt);
			i++;
		}
		if (ListenEscKey(sleepTimeBetweenPoints)) {
			cout << "you pressed ESC key. Totally " << i << " points have been recorded" << endl;
			break;
		}
		bReturn = GetCursorPos(&point);
	}

	return i;
}

/*
#include <Windows.h>：本例子的#include <Windows.h>已经被包括在#include <afxwin.h>里面了。
*/
bool BasicOperation::ListenEscKey(int sleepTime)
{
	int newTime = 0;
	long long endTs = 0LL;
	if (1 > sleepTime)
	{
		newTime = GetRandomTime(0, 0); // in case that 0 > sleepTime
	}
	else {
		newTime = GetRandomTime(sleepTime, 0);
	}
	endTs = GetCurrentTs() + newTime;

	while (1) {
		if (GetCurrentTs() > endTs) {
			break;
		}
		if (KEY_DOWN(ESC_KEY)) {
			return true;
		}
		Sleep(20);
	}
	return false;
}

/*
References:
基于C和C++将int与字符串类型相互转换：https://www.cnblogs.com/qinsun/p/10091910.html
《C++ Primer Plus第6版中文版》Page 272
*/
std::string BasicOperation::ConvertIntToString(vector<ScreenPoint>& pt_vector)
{
	string out_string = "";
	string temp = "";
	for (int i = 0; i < pt_vector.size(); i++)
	{
		temp = std::to_string(pt_vector[i].x) + "," + std::to_string(pt_vector[i].y) + "\n";
		out_string += temp;
		i++;
	}
	return out_string;
}

/*
《C++ Primer Plus第6版中文版》Page 272
*/
bool BasicOperation::WriteFile(const std::string& content, const std::string& filePath)
{
	if (1 > content.length()) {
		cout << "Please pass content for writing " << filePath << endl;
		return false;
	}
	ofstream fileOut;
	fileOut.open(filePath);
	if (!fileOut.is_open())
	{
		cout << "Cannot open " << filePath << endl;
		return false;
	}
	fileOut << content;
	return true;
}

/*
https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-mouse_event
#include <Windows.h>：本例子的#include <Windows.h>已经被包括在#include <afxwin.h>里面了。
*/
void BasicOperation::DragTheMap(const MouseTrace& mt)
{
	int x = GetRandomInt(mt.boxStartX, mt.boxEndX);
	int y = GetRandomInt(mt.boxStartY, mt.boxEndY);
	ScreenPoint pt = { x, y }, new_pt;
	new_pt = GetEndXY(mt, pt);
	mouse_event(MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE, x * 65535 / clientWidth, y * 65535 / clientHeight, 0, 0);
	Sleep(20);
	mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0);
	Sleep(20);
	mouse_event(MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE, new_pt.x * 65535 / clientWidth, new_pt.y * 65535 / clientHeight, 0, 0);
	Sleep(20);
	mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
}

/*
获取最终点的x, y值，放在自定义结构体ScreenPoint内
*/
ScreenPoint BasicOperation::GetEndXY(const MouseTrace& mt, ScreenPoint pt)
{
	ScreenPoint return_pt = pt;
	if (toRight == mt.moveDirection) {
		return_pt.x = pt.x + mt.movePixel;
	}
	else if (toBottom == mt.moveDirection) {
		return_pt.y = pt.y + mt.movePixel;
	}
	else if (toLeft == mt.moveDirection) {
		return_pt.x = pt.x - mt.movePixel;
	}
	else if (toTop == mt.moveDirection) {
		return_pt.y = pt.y - mt.movePixel;
	}
	return return_pt;
}

/*
检查mt这个MouseTrace结构体实例是否正确
*/
std::string BasicOperation::CheckMouseTraceStructure(const MouseTrace& mt)
{
	string errorMsg = "";
	if (10 > mt.movePixel) {
		errorMsg = std::to_string(mt.movePixel);
		return "mt.movePixel is too small to move: " + errorMsg;
	}
	if (0 > mt.boxEndX || 0 > mt.boxEndY || 0 > mt.boxStartX || 0 > mt.boxStartY) {
		errorMsg = std::to_string(mt.boxEndX) + "," + std::to_string(mt.boxEndY) + "," + std::to_string(mt.boxStartX) + "," + std::to_string(mt.boxStartY);
		return "mt has negative attribute(s): boxEndX, boxEndY, boxStartX, boxStartY == " + errorMsg;
	}
	if (clientWidth < mt.boxEndX || clientHeight < mt.boxEndY || clientWidth < mt.boxStartX || clientHeight < mt.boxStartY) {
		errorMsg = std::to_string(clientWidth) + "," + std::to_string(clientHeight) + "," + std::to_string(mt.boxEndX) + "," + std::to_string(mt.boxEndY) + \
			"," + std::to_string(mt.boxStartX) + "," + std::to_string(mt.boxStartY);
		return "mt has over large attribute(s): boxEndX, boxEndY, boxStartX, boxStartY == " + errorMsg;
	}

	if (toRight == mt.moveDirection) {
		if (clientWidth < mt.movePixel + mt.boxEndX) {
			errorMsg = std::to_string(mt.movePixel) + " + " + std::to_string(mt.boxEndX);
			return "clientWidth is smaller than mt.movePixel + mt.boxEndX: " + errorMsg;
		}
	}
	else if (toBottom == mt.moveDirection) {
		if (clientHeight < mt.movePixel + mt.boxEndY) {
			errorMsg = std::to_string(mt.movePixel) + " + " + std::to_string(mt.boxEndY);
			return "clientHeight is smaller than mt.movePixel + mt.boxEndY: " + errorMsg;
		}
	}
	else if (toLeft == mt.moveDirection) {
		if (mt.boxStartX < mt.movePixel) {
			errorMsg = std::to_string(mt.movePixel) + " > " + std::to_string(mt.boxStartX);
			return "mt.boxStartX < mt.movePixel: " + errorMsg;
		}
	}
	else if (toTop == mt.moveDirection) {
		if (mt.boxStartY < mt.movePixel) {
			errorMsg = std::to_string(mt.movePixel) + " > " + std::to_string(mt.boxStartY);
			return "mt.boxStartY < mt.movePixel: " + errorMsg;
		}
	}
	return "";
}

