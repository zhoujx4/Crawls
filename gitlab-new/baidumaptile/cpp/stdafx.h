/*
_WIN32_WINNT版本列表：https://blog.csdn.net/cai6811376/article/details/52637728
宏定义 _WIN32_WINNT=0x0400到底往哪加？https://bbs.csdn.net/topics/360159997
*/
//#ifndef _WIN32_WINNT
//#define _WIN32_WINNT _WIN32_WINNT_MAXVER // 0x0600 means Windows Server 2008
//#endif
//上面代码一直还没有调通；经常有报错，但是不影响exe文件执行。

/*
#define _AFXDLL
Managed C++ dll: #define _AFXDLL or do not use /MD[ d]?https://www.cnblogs.com/time-is-life/p/8543585.html
https://social.msdn.microsoft.com/Forums/vstudio/en-US/553fa850-5e6e-4ecb-a4eb-bbd81f8ff6b6/managed-c-dll-define-afxdll-or-do-not-use-md-d?forum=vcgeneral
中文版Visual Studio2019在项目 => 最后的...属性 => 配置属性 => 高级 => MFC的使用，这个项目里面设置成为：在共享DLL中使用MFC
*/

#ifndef STDAFX_H_
#define STDAFX_H_

#include <iostream>
#include <string>
#include <stdio.h>
#include <vector>
#include "BasicOperation.h"
#include "OpenCV.h"

#endif
