//don't use #pragma once, it cannot prevent damages from dulplicate files with different file names.
#ifndef OPEN_C_V_H_
#define OPEN_C_V_H_

#include <iostream>
#include <string>
#include <vector>
#include <opencv2/core.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/highgui.hpp>

#ifndef AFXWIN_H_
#define AFXWIN_H_
#include <afxwin.h>
#endif

/*
自定义InitAttribute结构体
*/
struct InitAttribute
{
	std::string rootPath;
	int clientWidth;
	int clientHeight;
	int windowWidth;
	int windowHeight;
};

class OpenCV
{
private:
	std::string name;
public:
	std::string rootPath;
	int clientWidth;
	int clientHeight;
	int windowWidth;
	int windowHeight;
	OpenCV(const InitAttribute& initAttributes);
	~OpenCV();
	void InitializeAttributes(const InitAttribute& initAttributes);
	int ShowImage( std::string& imageFilePath);
	void ScreenSnapshot(cv::Mat& src);
};

#endif
