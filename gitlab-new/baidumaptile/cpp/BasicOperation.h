//don't use #pragma once, it cannot prevent damages from dulplicate files with different file names.
#ifndef BASIC_OPERATION_H_
#define BASIC_OPERATION_H_

#include <fstream>
#include <iostream>
#include <string>
#include <sys/timeb.h>
#include <vector>

#define ESC_KEY 0x1B
#define KEY_DOWN(VK_NONAME) ((GetAsyncKeyState(VK_NONAME) & 0x8000) ? 1:0)

const int CHAR_ARRAY_SIZE = 8192; // 16384会报错
const int RANDOM_MIDTIME = 1500;
const int RANDOM_TIME_RANGE = 1000;

/*
下面的枚举和结构都是给DragTheMap使用的
由于无法引入Windows.h的POINT和CPoint结构体，只好自己定义这个ScreenPoint
*/
struct ScreenPoint
{
	int x;
	int y;
};
/* 这里需要特别注意的是：toRight是指鼠标向右移动；在地图上面这将导致地图向左移动（东经经度减少）！ */
enum FourDirections { toRight = 1, toBottom = 2, toLeft = 3, toTop = 4 };
struct MouseTrace
{
	int boxStartX;
	int boxStartY;
	int boxEndX;
	int boxEndY;
	int movePixel;
	FourDirections moveDirection;
};

class BasicOperation
{
private:
	std::string name;
public:
	std::string rootPath;
	int clientWidth = 1920;
	int clientHeight = 1080;
	int windowWidth = 1920;
	int windowHeight = 1080;

	BasicOperation();
	BasicOperation(const std::string& rootPathRef);
	~BasicOperation();
	void InitializeAttributes(const std::string& rootPathRef);
	std::string GetCwd(void);
	int GetFileNumberInDirectory(const std::string& folderPath);
	int GetRandomTime(int midtime = 0, int range = 0);
	int GetRandomInt(int minimal_int, int maximal_int);
	long long GetCurrentTs(void);
	bool CopyToClipboard(std::string dataToClipboard);
	void CtrlPaste(int x = 0, int y = 0);
	void ReadFileToAttribute(const std::string& filePath);
	int PrintXY(std::vector<ScreenPoint>& pt_vector, int sleepTimeBetweenPoints = 2000);
	bool ListenEscKey(int sleepTime = 5000);
	bool WriteFile(const std::string& content, const std::string& filePath);
	std::string ConvertIntToString(std::vector<ScreenPoint>& pt_vector);
	void DragTheMap(const MouseTrace& mt);
	ScreenPoint GetEndXY(const MouseTrace& mt, ScreenPoint pt);
	std::string CheckMouseTraceStructure(const MouseTrace& mt);

	// int ScreenSnapshot(const std::string& folderNameRef, const std::string& filePrefix);
	//将上面这个方法放置到OpenCV类里面了。
};

#endif
