# coding: utf-8

import datetime
import os
import sys
import six
import json
import warnings
from collections.abc import MutableMapping
from importlib import import_module
from . import settings_bmapm2

from scrapy.utils.deprecate import create_deprecated_class
from scrapy.exceptions import ScrapyDeprecationWarning

"""
	The following codes are mainly copied from Scrapy
"""
SETTINGS_PRIORITIES = {
	'default': 0,
	'command': 10,
	'project': 20,
	'spider': 30,
	'cmdline': 40,
}

def get_settings_priority(priority):
	"""
	Small helper function that looks up a given string priority in the
	:attr:`~scrapy.settings.SETTINGS_PRIORITIES` dictionary and returns its
	numerical value, or directly returns a given numerical priority.
	"""
	if isinstance(priority, six.string_types):
		return SETTINGS_PRIORITIES[priority]
	else:
		return priority

class SettingsAttribute(object):
	"""Class for storing data related to settings attributes.
	This class is intended for internal usage, you should try Settings class
	for settings configuration, not this one.
	"""

	def __init__(self, value, priority):
		self.value = value
		if isinstance(self.value, BaseSettings):
			self.priority = max(self.value.maxpriority(), priority)
		else:
			self.priority = priority

	def set(self, value, priority):
		"""Sets value if priority is higher or equal than current priority."""
		if priority >= self.priority:
			if isinstance(self.value, BaseSettings):
				value = BaseSettings(value, priority=priority)
			self.value = value
			self.priority = priority

	def __str__(self):
		return "<SettingsAttribute value={self.value!r} priority={self.priority}>".format(self=self)

	__repr__ = __str__

class BaseSettings( MutableMapping ):
	"""
	References:
		Python自悟：Python中的Dict and Set：https://www.jianshu.com/p/6439954d2417
		继承MutableMapping以后的BaseSettings是抽象类，下面settings = BaseSettings( values = value_dict )会报错
		需要采用scrapy框架的方法，定义class Settings(BaseSettings)来继承BaseSettings。todo...
	"""
	def __init__(self, values=None, priority="project" ):
		self.frozen = False
		self.attributes = {}
		self.update(values, priority)

	def get(self, name, default=None):
		"""
		Get a setting value without affecting its original type.

		:param name: the setting name
		:type name: string

		:param default: the value to return if no setting is found
		:type default: any
		"""
		return self[name] if self[name] is not None else default

	def update(self, values, priority="project"):
		"""
		Store key/value pairs with a given priority.

		This is a helper function that calls
		:meth:`~scrapy.settings.BaseSettings.set` for every item of ``values``
		with the provided ``priority``.

		If ``values`` is a string, it is assumed to be JSON-encoded and parsed
		into a dict with ``json.loads()`` first. If it is a
		:class:`~scrapy.settings.BaseSettings` instance, the per-key priorities
		will be used and the ``priority`` parameter ignored. This allows
		inserting/updating settings with different priorities with a single
		command.

		:param values: the settings names and values
		:type values: dict or string or :class:`~scrapy.settings.BaseSettings`

		:param priority: the priority of the settings. Should be a key of
			:attr:`~scrapy.settings.SETTINGS_PRIORITIES` or an integer
		:type priority: string or int
		"""
		self._assert_mutability()
		if isinstance(values, six.string_types):
			values = json.loads(values)
		if values is not None:
			if isinstance(values, BaseSettings):
				for name, value in six.iteritems(values):
					self.set(name, value, values.getpriority(name))
			else:
				for name, value in six.iteritems(values):
					self.set(name, value, priority)

	def getpriority(self, name):
		"""
		Return the current numerical priority value of a setting, or ``None`` if
		the given ``name`` does not exist.

		:param name: the setting name
		:type name: string
		"""
		if name not in self:
			return None
		return self.attributes[name].priority

	def set(self, name, value, priority="project"):
		"""
		Store a key/value attribute with a given priority.

		Settings should be populated *before* configuring the Crawler object
		(through the :meth:`~scrapy.crawler.Crawler.configure` method),
		otherwise they won't have any effect.

		:param name: the setting name
		:type name: string

		:param value: the value to associate with the setting
		:type value: any

		:param priority: the priority of the setting. Should be a key of
			:attr:`~scrapy.settings.SETTINGS_PRIORITIES` or an integer
		:type priority: string or int
		"""
		self._assert_mutability()
		priority = get_settings_priority(priority)
		# print( name )
		# print( self )
		# sys.exit(3)
		if name not in self:
			if isinstance(value, SettingsAttribute):
				self.attributes[name] = value
			else:
				self.attributes[name] = SettingsAttribute(value, priority)
		else:
			self.attributes[name].set(value, priority)

	def setmodule(self, module, priority='project'):
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
		self._assert_mutability()
		if isinstance(module, six.string_types):
			module = import_module(module)
		for key in dir(module):
			if key.isupper():
				self.set(key, getattr(module, key), priority)

	def _assert_mutability(self):
		if self.frozen:
			raise TypeError("Trying to modify an immutable Settings object")

	def __iter__(self):
		return iter(self.attributes)

	def __len__(self):
		return len(self.attributes)

	def __delitem__(self, name):
		self._assert_mutability()
		del self.attributes[name]

	def __setitem__(self, name, value):
		self.set(name, value)

	def __getitem__(self, opt_name):
		if opt_name not in self:
			return None
		return self.attributes[opt_name].value

	@property
	def overrides(self):
		warnings.warn("`Settings.overrides` attribute is deprecated and won't "
					  "be supported in Scrapy 0.26, use "
					  "`Settings.set(name, value, priority='cmdline')` instead",
					  category=ScrapyDeprecationWarning, stacklevel=2)
		try:
			o = self._overrides
		except AttributeError:
			self._overrides = o = _DictProxy(self, 'cmdline')
		return o

	@property
	def defaults(self):
		warnings.warn("`Settings.defaults` attribute is deprecated and won't "
					  "be supported in Scrapy 0.26, use "
					  "`Settings.set(name, value, priority='default')` instead",
					  category=ScrapyDeprecationWarning, stacklevel=2)
		try:
			o = self._defaults
		except AttributeError:
			self._defaults = o = _DictProxy(self, 'default')
		return o

class _DictProxy(MutableMapping):

	def __init__(self, settings, priority):
		self.o = {}
		self.settings = settings
		self.priority = priority

	def __len__(self):
		return len(self.o)

	def __getitem__(self, k):
		return self.o[k]

	def __setitem__(self, k, v):
		self.settings.set(k, v, priority=self.priority)
		self.o[k] = v

	def __delitem__(self, k):
		del self.o[k]

	def __iter__(self, k, v):
		return iter(self.o)

class Settings( BaseSettings ):
	"""
	Author: Scrapy
	This object stores Scrapy settings for the configuration of internal
	components, and can be used for any further customization.

	It is a direct subclass and supports all methods of
	:class:`~scrapy.settings.BaseSettings`. Additionally, after instantiation
	of this class, the new object will have the global settings
	described on :ref:`topics-settings-ref` already populated.
	"""

	def __init__( self, values=None, priority="project" ):
		# Do not pass kwarg values here. We don't want to promote user-defined
		# dicts, and we want to update, not replace, default dicts with the
		# values given by the user
		super(Settings, self).__init__()
		self.setmodule(settings_bmapm2, "spider")
		# Promote default dictionaries to BaseSettings instances for per-key
		# priorities
		for name, val in six.iteritems(self):
			if isinstance(val, dict):
				self.set(name, BaseSettings(val, "spider"), "spider")
		self.update(values, priority)

class CrawlerSettings(Settings):

	def __init__(self, settings_module=None, **kw):
		self.settings_module = settings_module
		Settings.__init__(self, **kw)

	def __getitem__(self, opt_name):
		if opt_name in self.overrides:
			return self.overrides[opt_name]
		if self.settings_module and hasattr(self.settings_module, opt_name):
			return getattr(self.settings_module, opt_name)
		if opt_name in self.defaults:
			return self.defaults[opt_name]
		return Settings.__getitem__(self, opt_name)

	def __str__(self):
		return "<CrawlerSettings module=%r>" % self.settings_module

CrawlerSettings = create_deprecated_class(
	'CrawlerSettings', CrawlerSettings,
	new_class_path='scrapy.settings.Settings')

def iter_default_settings():
	"""Return the default settings as an iterator of (name, value) tuples"""
	for name in dir(default_settings):
		if name.isupper():
			yield name, getattr(default_settings, name)


def overridden_settings(settings):
	"""Return a dict of the settings that have been overridden"""
	for name, defvalue in iter_default_settings():
		value = settings[name]
		if not isinstance(defvalue, dict) and value != defvalue:
			yield name, value

# 类似scrapy框架，可以用检查全部大写字母和下划线的方法自动生成本文件的key_list
# key_list = ["PROJECT_DEBUG", "PROJECT_PATH", "LOG_DIR", "OUTPUT_FOLDER_NAME", "CRAWLED_DIR", "BASE_URI", "LEVEL_Z", "BROWSER", "INPUT_FOLDER_NAME", ]
# value_dict = {}
# for key in key_list:
# 	value_dict[key] = eval(key)
# settings = BaseSettings( values = value_dict )
