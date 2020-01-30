#include <iostream>
#include <string>
#include <windows.h>
#include <winuser.h>
#include <ctime>
#include <sys/timeb.h>

#define KEY_DOWN(VK_NONAME) ((GetAsyncKeyState(VK_NONAME) & 0x8000) ? 1:0)

using namespace std;

const int RANDOM_MIDTIME = 1500;
const int RANDOM_TIME_RANGE = 1000;
int client_width = 1920;
int client_height = 1080;

int get_random_time(int midtime = 0, int range = 0)
{
	srand( time(0) );
	if ( 1 > midtime )
	{
		midtime = RANDOM_MIDTIME;
	}
	if ( 1 > range )
	{
		range = RANDOM_TIME_RANGE;
	}
	if ( range > midtime )
	{
		midtime = range;
	}
	return midtime - range / 2 + rand() % range;
	// rand() returns an int from 0 to RAND_MAX(2147483647)
}

void keyboard_scroll_home_or_end(bool y_down = true)
{
	if ( y_down )
	{
		keybd_event(0x11,0,0,0); // CTRL key
		keybd_event(0x23,0,0,0); // END key
		keybd_event(0x23,0,2,0);
		keybd_event(0x11,0,2,0);
	} else {
		keybd_event(0x11,0,0,0); // CTRL key
		keybd_event(0x24,0,0,0); // Home key
		keybd_event(0x24,0,2,0);
		keybd_event(0x11,0,2,0);
	}
	Sleep(50);
}

double get_current_ts()  
{
	double x, y;
	timeb t;
	ftime(&t);
	return t.time + t.millitm / 1000;
}

int click(int x = 0, int y = 0, int sleep_time = 5000)
{
	int new_time = 0;
	char esc_key = 0x1B;
	double end_ts = 0.0;
	
	// newer frontend requires to move the center of the screen
	mouse_event(MOUSEEVENTF_ABSOLUTE|MOUSEEVENTF_MOVE, 65535/2, 65535/2, 0, 0);
	Sleep(20);
	keyboard_scroll_home_or_end(true);
	mouse_event(MOUSEEVENTF_ABSOLUTE|MOUSEEVENTF_MOVE, x*65535/client_width, y*65535/client_height, 0, 0);
	Sleep(20);
	mouse_event(MOUSEEVENTF_LEFTDOWN,0,0,0,0);
	Sleep(20);
	mouse_event(MOUSEEVENTF_LEFTUP,0,0,0,0);
	if ( 1 > sleep_time )
	{
		new_time = get_random_time(0, 0); // in case that 0 > sleep_time
	} else {
		new_time = get_random_time(sleep_time, 0);
	}
	end_ts = get_current_ts() + new_time / 1000;

	while( 1 ){
		if ( get_current_ts() > end_ts ){
			break;
		}
		if( KEY_DOWN(esc_key) ){
			cout << "you pressed esc." << endl;
			return -1;
		}
		Sleep(20);
	}

	return new_time;
}

void initialize_screen_size(void)
{
	HWND hd = GetDesktopWindow();
	RECT rect;
	GetClientRect(hd, &rect);
	client_width = (rect.right - rect.left);
	client_height = (rect.bottom - rect.top); // 1920,1080
}

int main(int argc,char *argv[])
{
	/*
	This program is the C++ code for pressing Ctrl + END keys and then mouse click "Next Page" Button on 
	a webpage like the one at http://www.dianping.com/yueyang/ch10/g104
	After compiling, you are suggestted to rename the default exe file name from a.exe to ctrl.exe and then
	use this commandline "ctrl.exe 98 1750 1184 576" to run the exe file. After running this commandline, 
	you shall activate your browser window in 5 seconds. Meaning of these arguments:
	98: 	In a single cycle, the program will hit ctrl + END and left click mouse 1 time; 98 means the 
			program will run 98 cycles.
	1750: 	Depending on your Internet Bandwidth and download speed, you can set differnt time gap between
			two adjacent cycles. 1750 means 1.75 seconds
	1184:	the x value of the "Next Page" Button after Ctrl + End is hit
	576:	the y value of the "Next Page" Button after Ctrl + End is hit
	*/
	int number_of_pages = 1;
	int i = 0, x = 1285, y = 305; // 1270 to 1288; 300 to 306
	int sleep_time = 5000;
	int new_time = 0;
	
	initialize_screen_size();
	
	if ( 1 < argc && 0 < atoi( argv[1] ) ){
		number_of_pages = atoi(argv[1]);
	}
	if ( 2 < argc && 0 < atoi( argv[2] ) ){
		sleep_time = atoi(argv[2]);
	}
	if ( 3 < argc && 0 < atoi( argv[3] ) ){
		x = atoi(argv[3]);
	}
	if ( 4 < argc && 0 < atoi( argv[4] ) ){
		y = atoi(argv[4]);
	}

	Sleep( 5000 );
	for (i = 0; i < number_of_pages; i++)
	{
		keyboard_scroll_home_or_end(true);
		new_time = click(x, y, sleep_time);
		if ( -1 == new_time ){
			break;
		}
		cout << "clicked Page #" << i << ": slept " << new_time << " seconds." << endl;
	}
	return 0;
}
