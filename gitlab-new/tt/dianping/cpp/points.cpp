#include <windows.h>
#include <winuser.h>
#include <iostream>

using namespace std;

BOOL GetCursorPos( LPPOINT lpPoint );

int print_xy(int number_of_points = 10, int sleep_time_between_pts = 2000)
{
	// https://blog.csdn.net/yp18792574062/article/details/88351342 
	HWND hd = GetDesktopWindow();
	RECT rect;
	GetClientRect(hd, &rect);
	int client_width = (rect.right - rect.left);
	int client_height = (rect.bottom - rect.top);
	std::cout << "client width:" << client_width << std::endl; // 1920,1080
	std::cout << "client height:" << client_height << std::endl;
	
	GetWindowRect(hd, &rect);
	int window_width = (rect.right - rect.left);
	int window_height = (rect.bottom - rect.top);
	std::cout << "window width:" << window_width << std::endl; // 1920,1080
	std::cout << "window height:" << window_height << std::endl;

	// https://jingyan.baidu.com/article/b0b63dbf254a3b4a483070b8.html
	POINT P;
	int i;
	for( i = 0; i < number_of_points; i++ ){
		Sleep(sleep_time_between_pts);
		GetCursorPos(&P);
		cout << "Point # " << i << " : " << P.x << ","<< P.y << endl;
	}
	return 0;
}

int main(int argc,char *argv[])
{
	/*
	This program is the C++ code for display the x and y values of your mouse. After compiling, you are suggestted to rename the default exe 
	file name from a.exe to pts.exe and then use this commandline "pts.exe 3 5000" to run the exe file. After running this commandline, you 
	shall move your mouse to the point you want to collect the x and y values in 2 seconds. Meaning of these arguments:
	3: 		The program will run 3 cycles.
	5000: 	Depending on the speed you move your mouse, you can set differnt time gap between two adjacent cycles. 5000 means 5 seconds
	*/
	using namespace std;
	int number_of_points = 1;
	int sleep_time_between_pts = 2000;
	if ( 1 < argc && 0 < atoi( argv[1] ) ){
		number_of_points = atoi(argv[1]);
	}
	if ( 2 < argc && 0 < atoi( argv[2] ) ){
		sleep_time_between_pts = atoi(argv[2]);
	}
	print_xy(number_of_points, sleep_time_between_pts);
	return 0;
}
