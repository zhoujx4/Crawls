# coding: utf-8

import os
import sys
import six
from importlib import import_module

class BaseSettings(object ):
	"""
	在这里写这个BaseSettings，仅仅是为了以后升级到scrapy框架里面以及部署scrapyd分布式的时候不需要大量修改代码。
	References:
		Python自悟：Python中的Dict and Set：https://www.jianshu.com/p/6439954d2417
		继承MutableMapping以后的BaseSettings是抽象类，下面settings = BaseSettings( values = value_dict )会报错
		需要采用scrapy框架的方法，定义class Settings(BaseSettings)来继承BaseSettings。todo...
	"""
	def __init__(self, values=None ):
		self.attributes = {} if values is None else values

	def get(self, name, default=None):
		"""
		已经修改，与scrapy框架无相似之处
		"""
		return self.attributes[name] if name in self.attributes.keys() else default

	def set(self, name, value, priority="project"):
		"""
		Nothing similar to Scrapy here
		"""
		self.attributes[name] = value

	def setmodule(self, module):
		"""
		Store settings from a module with a given priority.

		This is a helper function that calls
		:meth:`~scrapy.settings.BaseSettings.set` for every globally declared
		uppercase variable of ``module`` with the provided ``priority``.

		:param module: the module or the path of the module
		:type module: module object or string

		:param priority: the priority of the settings. Should be a key of
			:attr:`~scrapy.settings.SETTINGS_PRIORITIES` or an integer
		:type priority: string or int
		"""
		if isinstance(module, six.string_types):
			module = import_module(module)
		for key in dir(module):
			if key.isupper():
				self.set(key, getattr(module, key))

settings = BaseSettings()
from . import settings_house163
settings.setmodule( settings_house163 )
