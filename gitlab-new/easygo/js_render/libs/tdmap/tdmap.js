(function () {
//window.onerror=function(){return false};
    var console = window.console || {
            log: function () {
            }
        };
    window.TD = window.TD || {};
    var TD = {Config: window.TD.Config || {}};
    (function () {
        var counter = 0;
        window.tdmap_instances = {};

        /**
         * TD框架的基类
         * @namespace
         * @name TD.BaseClass
         */
        TD.BaseClass = function (hc) {
            tdmap_instances[(this.hashCode = (hc || TD.BaseClass.guid()))] = this;
        };

        /** @ignore */
        TD.BaseClass.guid = function () {
            return "td_" + (counter++).toString(36);
        };


        /**
         * 根据参数(hashCode)的指定，返回对应的实例对象引用
         * @param {String} hashCode 需要获取实例的hashCode
         * @return {Object/Null} 如果存在的话，返回;否则返回Null。
         */
        window.Instance = TD.I = function (hashCode) {
            return tdmap_instances[hashCode];
        };

        /**
         * 释放对象所持有的资源。
         * 主要是自定义事件。
         * 好像没有将_listeners中绑定的事件剔除掉..
         */
        TD.BaseClass.prototype.dispose = function () {
            if (this.hashCode) {
                delete tdmap_instances[this.hashCode];
            }

            for (var i in this) {
                if (typeof this[i] != "function") {
                    delete this[i];
                }
            }
        };

        /**
         * 返回对象的hashCode，如果没有的话，添加一个新的hashCode并将其返回
         * @return {String} 对象的hashCode
         */
        TD.BaseClass.prototype.getHashCode = function () {
            if (!this.hashCode) {
                tdmap_instances[(this.hashCode = TD.BaseClass.guid())] = this;
            }
            return this.hashCode;
        };

        /**
         * 从tdmap_instances数组中将对象的引用删除掉。
         * 删除之后就无法使用TD.I()函数获取对象了。
         */
        TD.BaseClass.prototype.decontrol = function () {
            delete tdmap_instances[this.hashCode];
        };


        /**
         * 将source中的所有属性拷贝到target中。
         * @param {Object} target 属性的接收者
         * @param {Object} source 属性的来源
         * @return {Object} 返回的内容是o
         */
        TD.extend = function (target, source) {

            if (target && source && typeof (source) == "object") {
                for (var p in source) {
                    target[p] = source[p];
                }

                var prototype_fields = [
                    'constructor',
                    'hasOwnProperty',
                    'isPrototypeOf',
                    'propertyIsEnumerable',
                    'toLocaleString',
                    'toString',
                    'valueOf'
                ];

                for (var j = 0, key; j < prototype_fields.length; j++) {
                    key = prototype_fields[j];
                    if (Object.prototype.constructor.call(source, key)) {
                        target[key] = source[key];
                    }
                }
            }
            return target;
        };


    })();

    /**
     * 父类继承
     * @param {Object} parentClass
     * @param {Object} className
     */
    Function.prototype.inherits = function (parentClass, className) {
        var i, p, op = this.prototype, C = function () {
        };
        C.prototype = parentClass.prototype;
        p = this.prototype = new C();
        if (typeof (className) == "string") {
            p.className = className;
        }
        for (i in op) {
            p[i] = op[i];
        }
        this.prototype.constructor = op.constructor;
        op = C = null;
        return p;
    };

    /**
     * 自定义的事件对象
     * @namespace
     * @name TD.BaseEvent
     */
    TD.BaseEvent = function (type, target) {
        /**
         * 事件的名称
         * @type {String}
         */
        this.type = type;

        /**
         * 当事件发生之后处理结果的返回值
         * @type {Boolean}
         */
        this.returnValue = true;

        /**
         * 在事件被触发后传递的对象
         * @type {TD.BaseClass}
         */
        this.target = target || null;

        /**
         * 触发该事件的对象
         * @type {TD.BaseClass}
         */
        this.currentTarget = this.srcElement = null;

        /**
         * 作为阻止事件冒泡的一个标志参数
         * @type {Boolean}
         */
        this.cancelBubble = false;

        this.domEvent = null;
    };

    /**
     * 扩展TD.BaseClass来添加自定义事件
     * @param {String} type 自定义事件的名称
     * @param {Function} handler 自定义事件被触发时应该调用的回调函数
     * @param {String} key 可选参数，绑定到事件上的函数对应的索引key
     */
    TD.BaseClass.prototype.addEventListener = function (type, handler, key) {
        if (typeof handler != "function") {
            return;
        }
        if (!this._listeners) {
            this._listeners = {};
        }
        var t = this._listeners, id;
        if (typeof key == "string" && key) {
            if (!/[^\w\-]/.test(key)) {
                handler.hashCode = key;
                id = key;
            }
        }
        if (type.indexOf("on") != 0) {
            type = "on" + type;
        }
        if (typeof t[type] != "object") {
            t[type] = {};
        }
        id = id || TD.BaseClass.guid();
        handler.hashCode = id;
        t[type][id] = handler;
    };

    /**
     * 删除自定义事件中绑定的一个回调函数。如果第二个参数handler没有被
     * 绑定到对应的自定义事件中，什么也不做。
     * @param {String} type 自定义事件的名称
     * @param {Function} handler 需要删除的自定义事件的函数或者该函数对应的索引key
     */
    TD.BaseClass.prototype.removeEventListener = function (type, handler) {
        if (typeof handler == "function") {
            handler = handler.hashCode;
        } else if (typeof handler != "string") {
            return;
        }
        if (!this._listeners) {
            this._listeners = {};
        }
        if (type.indexOf("on") != 0) {
            type = "on" + type;
        }
        var t = this._listeners;
        if (!t[type]) {
            return;
        }
        if (t[type][handler]) {
            delete t[type][handler];
        }
    };

    /**
     * 清除掉自定义事件中绑定的所有回调函数。(慎用)
     * @param {String} type 自定义事件的名称
     */
    TD.BaseClass.prototype.clearEventListener = function (type) {
        if (!this._listeners) {
            this._listeners = {};
        }
        if (type.indexOf("on") != 0) {
            type = "on" + type;
        }
        var t = this._listeners;
        if (!t[type]) {
            return;
        }
        for (var handler in t[type]) {
            delete t[type][handler];
        }
    };

    /**
     * 派发自定义事件，使得绑定到自定义事件上面的函数都会被执行。
     * 但是这些绑定函数的执行顺序无法保证。
     * 处理会调用通过addEventListenr绑定的自定义事件回调函数之外，还会调用
     * 直接绑定到对象上面的自定义事件。例如：
     * myobj.onMyEvent = function(){}
     * myobj.addEventListener("onMyEvent", function(){});
     * @param {TD.BaseEvent} event 派发的自定义事件类型
     * @param {TD.BaseEvent} key 事件参数
     */
    TD.BaseClass.prototype.dispatchEvent = function (event, key) {
        if (!this._listeners) {
            this._listeners = {};
        }
        var i, t = this._listeners, p = event.type;
        event.target = event.srcElement = event.target || event.srcElement || this;
        event.currentTarget = this;

        key = key || {};
        for (var k in key) {
            event[k] = key[k];
        }

        if (typeof this[p] == "function") {
            this[p](event);
        }
        if (typeof t[p] == "object") {
            for (i in t[p]) {
                if (typeof t[p][i] == "function") {
                    t[p][i].call(this, event);
                }
            }
        }
        return event.returnValue;
    };
    /**
     * 是否是函数
     * @param {Mix}
     * @returns {Boolean}
     */
    function isFunction(func) {
        return typeof func == "function";
    }

    /**
     * 是否是数字
     * @param {Mix}
     * @returns {Boolean}
     */
    function isNumber(number) {
        return typeof number == "number";
    }

    /**
     * 是否是字符串
     * @param {Mix}
     * @returns {Boolean}
     */
    function isString(string) {
        return typeof string == "string";
    }

    /**
     * 是否定义
     * @param {Mix}
     * @returns {Boolean}
     */
    function isDefined(object) {
        return typeof object != "undefined";
    }

    /**
     * 是否为对象类型
     * @param {Mix}
     * @returns {Boolean}
     */
    function isObject(object) {
        return typeof object == 'object';
    }

    /**
     * 判断目标参数是否Array对象
     * @param {Mix}
     * @returns {boolean} 类型判断结果
     */
    function isArray(source) {
        return '[object Array]' == Object.prototype.toString.call(source);
    };
    /**
     * 判断字符串长度英文占1个字符，中文汉字占2个字符
     * @param {Object} str
     */
    function getBlen(str) {
        return str.replace(/[^\x00-\xff]/g, "01").length;
    }

    /*
     *获取鼠标相对于canvas 的距离
     */
    function captureMouse(element) {
        var mouse = {x: 0, y: 0, event: null};

        element.addEventListener('mousemove', function (event) {
            var bounding = element.getBoundingClientRect();
            var offsetLeft = bounding.left;
            var offsetTop = bounding.top;
            var body_scrollTop = document.body.scrollTop;
            var body_scrollLeft = document.body.scrollLeft;
            var x, y;
            x = event.pageX - offsetLeft - body_scrollLeft;
            y = event.pageY - offsetTop - body_scrollTop;
            mouse.x = x;
            mouse.y = y;
            mouse.event = event;
        }, false);

        return mouse;
    };
    /**
     * worker
     */
    var TD = TD || {}
    TD.workerMrg = {
        // url: TD.Config.workUrl || "http://" + location.host + "/dist/worker.js",
        url: TD.Config.workUrl || "http://" + location.host + "/aggregation-display/libs/tdmap/worker.js",
        // url: TD.Config.workUrl || "http://" + location.host + "/tobacco/js/libs/tdmap/worker.js",
        /**
         * 创建worker实例
         */
        createWorker: function () {
            //解决worker跨越问题
            //var bb = new Blob(["importScripts('http://localhost:8020/TDMap/dist/worker.js');"]);
            //var bb = new Blob(["importScripts('http://127.0.0.1:8020/map-library/dist/worker.js');"]);
            //		var bb = new Blob(["importScripts('http://192.168.1.103:8020/map-library/dist/worker.js');"]);

            var bb = new Blob(["importScripts('" + TD.workerMrg.url + "');"]);
            this.worker = new Worker(window.URL.createObjectURL(bb));
            //this.worker = new Worker('/TDMap/dist/worker.js');
            //接受消息
            this.worker.addEventListener('message', this.message);
            this.worker.onerror = function (e) {
                console.log('worker.onerror', e)
            }
        }

        /**
         * 接收消息
         */
        , message: function (e) {
            var data = e.data;
            var hashCode = data.request.hashCode;
            var msgId = data.request.msgId;
            var classPath = data.request.classPath;
            //console.log(TD.workerMrg.instances[classPath], hashCode+'_'+msgId, TD.workerMrg.instances[classPath] && TD.workerMrg.instances[classPath] == hashCode+'_'+msgId)
            if (TD.workerMrg.instances[classPath + '_' + hashCode] && TD.workerMrg.instances[classPath + '_' + hashCode] == hashCode + '_' + msgId) {
                TD.workerMrg.instances[hashCode + '_' + msgId](data.response.data);
            } else {
                delete TD.workerMrg.instances[hashCode + '_' + msgId];
            }
        }
        /**
         * 发送消息到worker
         * @param {JSON} data 发送的数据
         * @param {Function} callback 返回的回调
         */
        , postMessage: function (data, callback) {
            //console.log('callback', callback)
            var hashCode = data.request.hashCode;
            var msgId = data.request.msgId;
            var classPath = data.request.classPath;
            this.instances[hashCode + '_' + msgId] = callback;
            //worker队列唯一性判断，
            this.instances[classPath + '_' + hashCode] = hashCode + '_' + msgId;
            this.worker.postMessage(data);
        }

        /**
         * worker索引管理
         */
        , instances: {}

    };
//初始化分配worker线程
    TD.workerMrg.createWorker();

    /**
     * @fileoverview 关于矩形地理区域类文件
     * @author jiazheng
     * @version 1.0
     */
    /**
     * 矩形地理区域类;
     * @param {Point} south west 西南角，可选
     * @param {Point} north east 东北角，可选
     */
    function Bounds(sw, ne) {
        if (sw && !ne) {
            ne = sw;
        }
        this._sw = this._ne = null;
        this._swLng = this._swLat = null;
        this._neLng = this._neLat = null;
        if (sw) {
            this._sw = new Point(sw.lng, sw.lat);
            this._ne = new Point(ne.lng, ne.lat);
            this._swLng = sw.lng;
            this._swLat = sw.lat;
            this._neLng = ne.lng;
            this._neLat = ne.lat;
        }
    }

    TD.extend(Bounds.prototype, {
        /**
         * 矩形是否为空，当sw或ne为空时，返回true
         * @returns Boolean
         */
        isEmpty: function () {
            return !this._sw || !this._ne;
        },
        /**
         * 判断矩形区域是否与其他矩形区域相等
         * @param Bounds
         */
        equals: function (other) {
            if (!(other instanceof Bounds) ||
                this.isEmpty()) {
                return false;
            }
            return this.getSouthWest().equals(other.getSouthWest()) && this.getNorthEast().equals(other.getNorthEast());
        },
        /**
         * 获取西南角坐标
         */
        getSouthWest: function () {
            return this._sw;
        },
        /**
         * 获取东北角坐标
         */
        getNorthEast: function () {
            return this._ne;
        },
        /**
         * 返回该区域(Bounds)是否包含指定的区域(Bounds)
         * @param {Bounds} bounds
         * @return {Boolean} 返回true.
         */
        containsBounds: function (bounds) {
            if (!(bounds instanceof Bounds) ||
                this.isEmpty() ||
                bounds.isEmpty()) {
                return false;
            }

            return (bounds._swLng > this._swLng && bounds._neLng < this._neLng && bounds._swLat > this._swLat && bounds._neLat < this._neLat);
        },
        /**
         * 返回该区域的中心点地理坐标
         * @return {Point} 地理点坐标对象.
         */
        getCenter: function () {
            if (this.isEmpty()) {
                return null;
            }
            return new Point((this._swLng + this._neLng) / 2, (this._swLat + this._neLat) / 2);
        },
        /**
         * 返回该项矩形区域与指定矩形区域的交集，不相交返回空
         * @param {Bounds} bounds 指定的地理矩形区域
         * @return {Bounds|Null} 返回相交的Bounds，否则为null.
         */
        intersects: function (bounds) {
            if (!(bounds instanceof Bounds)) {
                return null;
            }
            if (Math.max(bounds._swLng, bounds._neLng) < Math.min(this._swLng, this._neLng) ||
                Math.min(bounds._swLng, bounds._neLng) > Math.max(this._swLng, this._neLng) ||
                Math.max(bounds._swLat, bounds._neLat) < Math.min(this._swLat, this._neLat) ||
                Math.min(bounds._swLat, bounds._neLat) > Math.max(this._swLat, this._neLat)) {
                return null;
            }

            var newMinX = Math.max(this._swLng, bounds._swLng);
            var newMaxX = Math.min(this._neLng, bounds._neLng);
            var newMinY = Math.max(this._swLat, bounds._swLat);
            var newMaxY = Math.min(this._neLat, bounds._neLat);

            return new Bounds(new Point(newMinX, newMinY), new Point(newMaxX, newMaxY));
        },
        /**
         * 返回该区域(Bounds)是否包含指定的点(Point) ;
         * @param {Point} point 点对象
         * @return {Boolean} 布尔值,包含:true,不包含:false;.
         */
        containsPoint: function (point) {
            if (!(point instanceof Point) ||
                this.isEmpty()) {
                return false;
            }
            return (point.lng >= this._swLng && point.lng <= this._neLng && point.lat >= this._swLat && point.lat <= this._neLat);
        },
        /**
         * 扩展一个地理点的bounds区域
         * @param Point point点对象.
         * @return ;.
         */
        extend: function (point) {
            if (!(point instanceof Point)) {
                return;
            }
            var lng = point.lng, lat = point.lat;
            if (!this._sw) {
                this._sw = new Point(0, 0);
            }
            if (!this._ne) {
                this._ne = new Point(0, 0);
            }
            if (!this._swLng || this._swLng > lng) {
                this._sw.lng = this._swLng = lng;
            }
            if (!this._neLng || this._neLng < lng) {
                this._ne.lng = this._neLng = lng;
            }
            if (!this._swLat || this._swLat > lat) {
                this._sw.lat = this._swLat = lat;
            }
            if (!this._neLat || this._neLat < lat) {
                this._ne.lat = this._neLat = lat;
            }
        },
        /**
         * 返回地理区域跨度，用坐标表示
         * @return Point
         */
        toSpan: function () {
            if (this.isEmpty()) {
                return new Point(0, 0);
            }
            return new Point(Math.abs(this._neLng - this._swLng), Math.abs(this._neLat - this._swLat));
        }
    });

//本算法的思想是把地图分成多个网格，当要计算的点落入某个网格时，将选取该网格最近的点进行匹配转换。
//使用尽量多的参考点，形成格网,选取的点越多，格网越密集，格网四边形越趋近于正方形，则精度越高
//目前点集形成格网精度10m
    var baidu = baidu || {};

    function CoordTrans() {
    }

    TD.extend(CoordTrans, {
        num: {
            bj: {num: Math.sin(Math.PI / 4), num2: Math.sin(Math.PI / 6)},
            gz: {num: Math.sin(Math.PI / 4), num2: Math.sin(Math.PI / 4)},
            sz: {num: Math.sin(Math.PI / 4), num2: Math.sin(Math.PI / 4)},
            sh: {num: Math.sin(Math.PI / 4), num2: Math.sin(Math.PI / 4)}
        },
        //此处为配准使用的参考点
        correct_pts: {
            bj: [
                {j: 116.305687, w: 39.990912, utm_x: 12947230.73, utm_y: 4836903.65, x: 630412, y: 547340},
                {j: 116.381837, w: 40.000198, utm_x: 12955707.8, utm_y: 4838247.62, x: 667412, y: 561832},
                {j: 116.430651, w: 39.995216, utm_x: 12961141.81, utm_y: 4837526.55, x: 686556, y: 573372},
                {j: 116.474111, w: 39.976323, utm_x: 12965979.81, utm_y: 4834792.55, x: 697152, y: 586816},
                {j: 116.280328, w: 39.953159, utm_x: 12944407.75, utm_y: 4831441.53, x: 603272, y: 549976},
                {j: 116.316117, w: 39.952496, utm_x: 12948391.8, utm_y: 4831345.64, x: 618504, y: 557872},
                {j: 116.350477, w: 39.938107, utm_x: 12952216.78, utm_y: 4829264.65, x: 627044, y: 568220},
                {j: 116.432025, w: 39.947158, utm_x: 12961294.76, utm_y: 4830573.59, x: 666280, y: 584016},
                {j: 116.46873, w: 39.949516, utm_x: 12965380.79, utm_y: 4830914.63, x: 683328, y: 591444},
                {j: 116.280077, w: 39.913823, utm_x: 12944379.8, utm_y: 4825753.62, x: 586150, y: 558552},
                {j: 116.308625, w: 39.91374, utm_x: 12947557.79, utm_y: 4825741.62, x: 598648, y: 564732},
                {j: 116.369853, w: 39.912979, utm_x: 12954373.73, utm_y: 4825631.62, x: 624561, y: 578039},
                {j: 116.433552, w: 39.914694, utm_x: 12961464.75, utm_y: 4825879.53, x: 652972, y: 591348},
                {j: 116.457034, w: 39.914273, utm_x: 12964078.78, utm_y: 4825818.67, x: 663028, y: 596444},
                {j: 116.490927, w: 39.914127, utm_x: 12967851.77, utm_y: 4825797.57, x: 677968, y: 604188},
                {j: 116.483839, w: 39.877198, utm_x: 12967062.73, utm_y: 4820460.67, x: 658596, y: 610312},
                {j: 116.405777, w: 39.864461, utm_x: 12958372.82, utm_y: 4818620.62, x: 619256, y: 596088},
                {j: 116.35345, w: 39.859774, utm_x: 12952547.74, utm_y: 4817943.6, x: 594633, y: 585851},
                {j: 116.403818, w: 39.9141, utm_x: 12958154.74, utm_y: 4825793.66, x: 639699, y: 585226},
                {j: 116.318111, w: 39.891101, utm_x: 12948613.78, utm_y: 4822469.56, x: 592856, y: 571480},
                {j: 116.413047, w: 39.907238, utm_x: 12959182.12, utm_y: 4824801.76, x: 640680, y: 588704},
                {j: 116.390843, w: 39.906113, utm_x: 12956710.35, utm_y: 4824639.16, x: 630620, y: 584108},
                {j: 116.446527, w: 39.899438, utm_x: 12962909.14, utm_y: 4823674.4, x: 651752, y: 597416},
                {j: 116.388665, w: 39.95527, utm_x: 12956467.9, utm_y: 4831746.87, x: 650656, y: 572800},
                {j: 116.398343, w: 39.939704, utm_x: 12957545.26, utm_y: 4829495.6, x: 648036, y: 578452},
                {j: 116.355101, w: 39.973581, utm_x: 12952731.53, utm_y: 4834395.82, x: 643268, y: 560944},
                {j: 116.380727, w: 39.88464, utm_x: 12955584.23, utm_y: 4821535.94, x: 616920, y: 586496},
                {j: 116.360843, w: 39.946452, utm_x: 12953370.73, utm_y: 4830471.48, x: 635293, y: 568765},
                {j: 116.340955, w: 39.973421, utm_x: 12951156.79, utm_y: 4834372.67, x: 638420, y: 558632},
                {j: 116.322585, w: 40.023941, utm_x: 12949111.83, utm_y: 4841684.79, x: 652135, y: 543802},
                {j: 116.356486, w: 39.883341, utm_x: 12952885.71, utm_y: 4821348.24, x: 606050, y: 581443},
                {j: 116.339592, w: 39.992259, utm_x: 12951005.06, utm_y: 4837098.59, x: 645664, y: 554400},
                {j: 116.3778, w: 39.86392, utm_x: 12955258.4, utm_y: 4818542.48, x: 606848, y: 590328},
                {j: 116.377354, w: 39.964124, utm_x: 12955208.75, utm_y: 4833027.64, x: 649911, y: 568581},
                {j: 116.361837, w: 39.963897, utm_x: 12953481.39, utm_y: 4832994.8, x: 643286, y: 565175},
                {j: 116.441397, w: 39.939403, utm_x: 12962338.06, utm_y: 4829452.07, x: 666772, y: 587728},
                {j: 116.359176, w: 40.006631, utm_x: 12953185.16, utm_y: 4839178.78, x: 660440, y: 555411}
            ],
            sz: [
                {
                    "w": 22.498861,
                    "utm_x": 12677279.029193671,
                    "utm_y": 2555027.9501714734,
                    "j": 113.880696,
                    "y": 1104472,
                    "x": 947240
                },
                {
                    "w": 22.500706,
                    "utm_x": 12683920.978881944,
                    "utm_y": 2555248.973138607,
                    "j": 113.940361,
                    "y": 1122320,
                    "x": 974864
                },
                {
                    "w": 22.576848,
                    "utm_x": 12675897.984563945,
                    "utm_y": 2564373.058056766,
                    "j": 113.86829,
                    "y": 1074048,
                    "x": 979136
                },
                {
                    "w": 22.55689,
                    "utm_x": 12680064.05051775,
                    "utm_y": 2561981.0013635466,
                    "j": 113.905714,
                    "y": 1092484,
                    "x": 986240
                },
                {
                    "w": 22.58066,
                    "utm_x": 12678671.98513852,
                    "utm_y": 2564829.983373251,
                    "j": 113.893209,
                    "y": 1080528,
                    "x": 992088
                },
                {
                    "w": 22.595751,
                    "utm_x": 12678298.949465925,
                    "utm_y": 2566638.9913895614,
                    "j": 113.889858,
                    "y": 1074484,
                    "x": 997960
                },
                {
                    "w": 22.557499,
                    "utm_x": 12684523.001238672,
                    "utm_y": 2562053.9875916084,
                    "j": 113.945769,
                    "y": 1104696,
                    "x": 1004564
                },
                {
                    "w": 22.648419,
                    "utm_x": 12676422.97299485,
                    "utm_y": 2572954.0513219936,
                    "j": 113.873006,
                    "y": 1051384,
                    "x": 1015916
                },
                {
                    "w": 22.562664,
                    "utm_x": 12690460.958807131,
                    "utm_y": 2562673.0054078405,
                    "j": 113.99911,
                    "y": 1119860,
                    "x": 1030228
                },
                {
                    "w": 22.646618,
                    "utm_x": 12683008.037804369,
                    "utm_y": 2572738.0652955617,
                    "j": 113.93216,
                    "y": 1070324,
                    "x": 1041496
                },
                {
                    "w": 22.571091,
                    "utm_x": 12695789.992135335,
                    "utm_y": 2563683.019582462,
                    "j": 114.046981,
                    "y": 1131924,
                    "x": 1055628
                },
                {
                    "w": 22.704467,
                    "utm_x": 12682276.994753957,
                    "utm_y": 2579677.075645295,
                    "j": 113.925593,
                    "y": 1048536,
                    "x": 1066348
                },
                {
                    "w": 22.547152,
                    "utm_x": 12702917.96800879,
                    "utm_y": 2560813.9850610085,
                    "j": 114.111012,
                    "y": 1160352,
                    "x": 1072596
                },
                {
                    "w": 22.546192,
                    "utm_x": 12704502.952164687,
                    "utm_y": 2560698.9417545213,
                    "j": 114.12525,
                    "y": 1165256,
                    "x": 1078452
                },
                {
                    "w": 22.5714,
                    "utm_x": 12702350.00978689,
                    "utm_y": 2563720.0558210905,
                    "j": 114.10591,
                    "y": 1150556,
                    "x": 1081960
                },
                {
                    "w": 22.555004,
                    "utm_x": 12704883.001041513,
                    "utm_y": 2561754.9738317807,
                    "j": 114.128664,
                    "y": 1163304,
                    "x": 1084172
                },
                {
                    "w": 22.551925,
                    "utm_x": 12706255.028694374,
                    "utm_y": 2561385.978019464,
                    "j": 114.140989,
                    "y": 1168216,
                    "x": 1088116
                },
                {
                    "w": 22.693756,
                    "utm_x": 12690318.02302569,
                    "utm_y": 2578392.0635360866,
                    "j": 113.997826,
                    "y": 1075100,
                    "x": 1092860
                },
                {
                    "w": 22.573769,
                    "utm_x": 12705731.042149788,
                    "utm_y": 2564004.003107545,
                    "j": 114.136282,
                    "y": 1159404,
                    "x": 1096572
                },
                {
                    "w": 22.583238,
                    "utm_x": 12706369.021093281,
                    "utm_y": 2565139.002548978,
                    "j": 114.142013,
                    "y": 1157896,
                    "x": 1103632
                },
                {
                    "w": 22.605844,
                    "utm_x": 12704694.980375737,
                    "utm_y": 2567848.984570506,
                    "j": 114.126975,
                    "y": 1145540,
                    "x": 1107972
                },
                {
                    "w": 22.637228,
                    "utm_x": 12702545.043656897,
                    "utm_y": 2571612.010208761,
                    "j": 114.107662,
                    "y": 1128764,
                    "x": 1114460
                },
                {
                    "w": 22.62496,
                    "utm_x": 12707132.013185183,
                    "utm_y": 2570140.9407190788,
                    "j": 114.148867,
                    "y": 1145732,
                    "x": 1127028
                },
                {
                    "w": 22.644524,
                    "utm_x": 12707016.01701364,
                    "utm_y": 2572486.9446672536,
                    "j": 114.147825,
                    "y": 1138800,
                    "x": 1135876
                },
                {
                    "w": 22.640188,
                    "utm_x": 12711515.0431873,
                    "utm_y": 2571966.966986786,
                    "j": 114.18824,
                    "y": 1152692,
                    "x": 1151836
                },
                {
                    "w": 22.59807,
                    "utm_x": 12720011.039168343,
                    "utm_y": 2566916.995355996,
                    "j": 114.26456,
                    "y": 1191212,
                    "x": 1165180
                },
                {
                    "w": 22.668221,
                    "utm_x": 12714081.987256048,
                    "utm_y": 2575329.007304823,
                    "j": 114.211299,
                    "y": 1150576,
                    "x": 1175404
                },
                {
                    "w": 22.702591,
                    "utm_x": 12717292.031020584,
                    "utm_y": 2579452.0022288463,
                    "j": 114.240135,
                    "y": 1148204,
                    "x": 1204600
                },
                {
                    "w": 22.731786,
                    "utm_x": 12717795.9798388,
                    "utm_y": 2582955.0308636553,
                    "j": 114.244662,
                    "y": 1139532,
                    "x": 1220540
                },
                {
                    "w": 22.727494,
                    "utm_x": 12720675.957721734,
                    "utm_y": 2582439.9980541077,
                    "j": 114.270533,
                    "y": 1148992,
                    "x": 1230084
                },
                {
                    "w": 22.716335,
                    "utm_x": 12725500.040345404,
                    "utm_y": 2581101.0132384477,
                    "j": 114.313868,
                    "y": 1166316,
                    "x": 1244102
                }
            ],
            gz: [
                {j: 113.335098, w: 23.147289, utm_x: 12616542.68, utm_y: 2632892.7, x: 1129109, y: 1073920},
                {j: 113.320932, w: 23.146956, utm_x: 12614965.71, utm_y: 2632852.62, x: 1125620, y: 1071640},
                {j: 113.321435, w: 23.140119, utm_x: 12615021.7, utm_y: 2632029.65, x: 1124032, y: 1072882},
                {j: 113.321471, w: 23.119165, utm_x: 12615025.71, utm_y: 2629507.68, x: 1118932, y: 1076530},
                {j: 113.340201, w: 23.118616, utm_x: 12617110.75, utm_y: 2629441.61, x: 1123238, y: 1079667},
                {j: 113.358068, w: 23.116323, utm_x: 12619099.71, utm_y: 2629165.66, x: 1126968, y: 1083116},
                {j: 113.357529, w: 23.131271, utm_x: 12619039.71, utm_y: 2630964.68, x: 1130508, y: 1080440},
                {j: 113.365811, w: 23.150595, utm_x: 12619961.67, utm_y: 2633290.66, x: 1137205, y: 1078567},
                {j: 113.294145, w: 23.118467, utm_x: 12611983.76, utm_y: 2629423.68, x: 1112245, y: 1072043},
                {j: 113.28615, w: 23.121525, utm_x: 12611093.75, utm_y: 2629791.7, x: 1110993, y: 1070197},
                {j: 113.307152, w: 23.055497, utm_x: 12613431.71, utm_y: 2621847.21, x: 1100144, y: 1085123},
                {j: 113.333445, w: 23.052687, utm_x: 12616358.66, utm_y: 2621509.2, x: 1105784, y: 1089948},
                {j: 113.347476, w: 23.048755, utm_x: 12617920.6, utm_y: 2621036.24, x: 1108099, y: 1093064},
                {j: 113.385774, w: 23.036574, utm_x: 12622183.96, utm_y: 2619571.12, x: 1113850, y: 1101834},
                {j: 113.364185, w: 22.89798, utm_x: 12619780.66, utm_y: 2602910.64, x: 1073186, y: 1123374},
                {j: 113.404577, w: 22.906481, utm_x: 12624277.13, utm_y: 2603932.06, x: 1084888, y: 1128692},
                {j: 113.430856, w: 22.913156, utm_x: 12627202.52, utm_y: 2604734.12, x: 1092892, y: 1131761},
                {j: 113.384554, w: 22.933021, utm_x: 12622048.15, utm_y: 2607121.32, x: 1086975, y: 1120403},
                {j: 113.263566, w: 23.146333, utm_x: 12608579.68, utm_y: 2632777.63, x: 1111742, y: 1062098},
                {j: 113.239213, w: 23.152996, utm_x: 12605868.69, utm_y: 2633579.69, x: 1107616, y: 1056740},
                {j: 113.253865, w: 23.131628, utm_x: 12607499.76, utm_y: 2631007.65, x: 1105912, y: 1062966},
                {j: 113.240767, w: 23.088434, utm_x: 12606041.68, utm_y: 2625809.7, x: 1092270, y: 1068184},
                {j: 113.279628, w: 23.088284, utm_x: 12610367.72, utm_y: 2625791.65, x: 1101412, y: 1074883},
                {j: 113.462271, w: 23.107058, utm_x: 12630699.66, utm_y: 2628050.7, x: 1148752, y: 1101736},
                {j: 113.401618, w: 23.052957, utm_x: 12623947.73, utm_y: 2621541.68, x: 1121925, y: 1101535},
                {j: 113.422504, w: 23.05905, utm_x: 12626272.77, utm_y: 2622274.61, x: 1128470, y: 1104049},
                {j: 113.362506, w: 23.107149, utm_x: 12619593.75, utm_y: 2628061.65, x: 1125835, y: 1085505},
                {j: 113.419629, w: 23.143176, utm_x: 12625952.73, utm_y: 2632397.61, x: 1148133, y: 1089052},
                {j: 113.23315, w: 23.062251, utm_x: 12605193.75, utm_y: 2622659.67, x: 1084184, y: 1071368},
                {j: 113.314525, w: 23.101412, utm_x: 12614252.48, utm_y: 2627371.29, x: 1113011, y: 1078426},
                {j: 113.307947, w: 23.131369, utm_x: 12613520.21, utm_y: 2630976.47, x: 1118622, y: 1072198}
            ],
            sh: [
                {j: 121.524411, w: 31.245875, utm_x: 13528182.75, utm_y: 3642354.51, x: 1086581, y: 1065728},
                {j: 121.419229, w: 31.244887, utm_x: 13516473.81, utm_y: 3642226.51, x: 1032616, y: 1029148},
                {j: 121.405637, w: 31.237871, utm_x: 13514960.74, utm_y: 3641317.54, x: 1022724, y: 1027244},
                {j: 121.415348, w: 31.222879, utm_x: 13516041.78, utm_y: 3639375.47, x: 1018548, y: 1036980},
                {j: 121.422561, w: 31.224261, utm_x: 13516844.73, utm_y: 3639554.48, x: 1022976, y: 1038908},
                {j: 121.412581, w: 31.204148, utm_x: 13515733.75, utm_y: 3636949.48, x: 1006568, y: 1043696},
                {j: 121.443025, w: 31.206202, utm_x: 13519122.8, utm_y: 3637215.49, x: 1022656, y: 1053704},
                {j: 121.524061, w: 31.246917, utm_x: 13528143.79, utm_y: 3642489.52, x: 1082052, y: 1064124},
                {j: 121.529343, w: 31.217769, utm_x: 13528731.78, utm_y: 3638713.59, x: 1072696, y: 1079064},
                {j: 121.530268, w: 31.210341, utm_x: 13528834.75, utm_y: 3637751.53, x: 1068748, y: 1082416},
                {j: 121.511601, w: 31.227303, utm_x: 13526756.73, utm_y: 3639948.53, x: 1069276, y: 1068716},
                {j: 121.4966, w: 31.243614, utm_x: 13525086.81, utm_y: 3642061.58, x: 1071220, y: 1056805},
                {j: 121.485021, w: 31.26138, utm_x: 13523797.82, utm_y: 3644363.54, x: 1075708, y: 1045540},
                {j: 121.465114, w: 31.278803, utm_x: 13521581.76, utm_y: 3646621.48, x: 1073740, y: 1031268},
                {j: 121.454784, w: 31.266566, utm_x: 13520431.82, utm_y: 3645035.58, x: 1063591, y: 1033191},
                {j: 121.46851, w: 31.24951, utm_x: 13521959.81, utm_y: 3642825.48, x: 1060200, y: 1044520},
                {j: 121.446384, w: 31.248422, utm_x: 13519496.73, utm_y: 3642684.51, x: 1048784, y: 1037750},
                {j: 121.509499, w: 31.246469, utm_x: 13526522.73, utm_y: 3642431.47, x: 1079309, y: 1060105},
                {j: 121.481643, w: 31.283943, utm_x: 13523421.78, utm_y: 3647287.68, x: 1087096, y: 1035304},
                {j: 121.508054, w: 31.280609, utm_x: 13526361.87, utm_y: 3646855.56, x: 1098432, y: 1045648},
                {j: 121.493854, w: 31.19121, utm_x: 13524781.12, utm_y: 3635274.07, x: 1039624, y: 1077288},
                {j: 121.500079, w: 31.185541, utm_x: 13525474.09, utm_y: 3634540.04, x: 1039960, y: 1081640},
                {j: 121.484482, w: 31.202846, utm_x: 13523737.82, utm_y: 3636780.87, x: 1041388, y: 1069232},
                {j: 121.480877, w: 31.189587, utm_x: 13523336.51, utm_y: 3635063.92, x: 1032484, y: 1073640},
                {j: 121.502652, w: 31.195209, utm_x: 13525760.52, utm_y: 3635791.9, x: 1046384, y: 1078728}
            ]
        },
        getLnglatIndex: function (city, x, y) {
            var leftTop = 0;
            var rightBottom = 0;
            var minDis = 10000000, secMinDis = 1000000000;
            for (var i = 0; i < this.correct_pts[city].length; i++) {
                var dis = this.getDis(this.correct_pts[city][i].x, this.correct_pts[city][i].y, x, y);
                if (dis < secMinDis) {
                    if (dis < minDis) {
                        secMinDis = minDis;
                        minDis = dis;
                        rightBottom = leftTop;
                        leftTop = i;
                    } else {
                        sedMinDis = dis;
                        rightBottom = i;
                    }
                }
            }
            return {lt: leftTop, rb: rightBottom};
        },
        getOMapIndex_mm: function (city, utm_x, utm_y) {
            var leftTop = 0;
            var rightBottom = 0;
            var minDis = 1294723000, secMinDis = 1294723000;
            for (var i = 0; i < this.correct_pts[city].length; i++) {
                //alert(correct_pts[i].j +',jgh,'+correct_pts[i].w+',jgh,'+j+',jgh,'+w);
                var dis = this.getDis(this.correct_pts[city][i].utm_x, this.correct_pts[city][i].utm_y, utm_x, utm_y);
                //alert(dis);
                if (dis < secMinDis) {
                    if (dis < minDis) {
                        secMinDis = minDis;
                        minDis = dis;
                        rightBottom = leftTop;
                        leftTop = i;
                    } else {
                        sedMinDis = dis;
                        rightBottom = i;
                    }

                }
                //alert(dis +',jgh,'+leftTop+',jgh,'+rightBottom+',jgh,'+minDis+',jgh,'+secMinDis);
            }
            return {lt: leftTop, rb: rightBottom};
        },

        getDis: function (x, y, x1, y1) {
            return Math.abs(x - x1) + Math.abs(y - y1);
        },
        //从标准平面坐标得到地图坐标
        toMap: function (city, x, y) {
            var x2 = (x - y) * this.num[city].num;
            var y2 = (x + y) * this.num[city].num * this.num[city].num2;

            return {x: x2, y: y2};
        },
        //从地图坐标得到标准平面坐标
        fromMap: function (city, x, y) {
            y = y / this.num[city].num2;
            var x2 = (x + y) / (this.num[city].num * 2);
            var y2 = (y - x) / (this.num[city].num * 2);

            return {x: x2, y: y2};
        },
        //得到小范围地图精度
        getDgPix_mm: function (city, index0, index1) {
            //var index0=0;
            //var index1=1;
            var px_1 = this.fromMap(city, this.correct_pts[city][index0].x, this.correct_pts[city][index0].y);
            var px_2 = this.fromMap(city, this.correct_pts[city][index1].x, this.correct_pts[city][index1].y);

            var x_1 = px_1.x, y_1 = px_1.y;
            var x_2 = px_2.x, y_2 = px_2.y;
            //var dj1=gpsToDegree(correct_pts[index0].j),dw1=gpsToDegree(correct_pts[index0].w);
            //var dj2=gpsToDegree(correct_pts[index1].j),dw2=gpsToDegree(correct_pts[index1].w);
            var dj1 = this.correct_pts[city][index0].utm_x, dw1 = this.correct_pts[city][index0].utm_y;
            var dj2 = this.correct_pts[city][index1].utm_x, dw2 = this.correct_pts[city][index1].utm_y;
            //alert(dj1+','+dj2+','+dw1+','+dw2+','+x_1+','+x_2+','+y_1+','+y_2);
            var a = Math.abs((dj2 - dj1) * 100000 / (x_2 - x_1));
            var b = Math.abs((dw2 - dw1) * 100000 / (y_2 - y_1));
            //a,b每十万像素对应的经纬度
            //alert(a+',ddddxy,'+b);
            return {j: a, w: b, x: 100000 / a, y: 100000 / b};
        },
        //从经纬度得到地图像素值,如需将地图坐标转换成经纬则反过来算即可
        //小范围内地图满足线性关系
        getPx_mm: function (city, utm_x, utm_y, index0, index1) {
            //var index0=0;
            //var index1=1;
            var px_src = this.correct_pts[city][index0];
            var gp_src = this.correct_pts[city][index0];
            var dgPix = this.getDgPix_mm(city, index0, index1);
            var px_1 = this.fromMap(city, px_src.x, px_src.y);
            //var dj1=gpsToDegree(gp_src.j),dw1=gpsToDegree(gp_src.w);
            var dj1 = gp_src.utm_x, dw1 = gp_src.utm_y;
            //var dj=gpsToDegree(j_arr),dw=gpsToDegree(w_arr);
            var dj = utm_x, dw = utm_y;

            var x_1 = px_1.x;
            var y_1 = px_1.y;

            var dj_s = dj - dj1, dw_s = dw - dw1;
            var x = dj_s * dgPix.x + x_1;
            var y = -dw_s * dgPix.y + y_1;
            //alert(dgPix.x+',xy,'+dgPix.y);

            var r = this.toMap(city, x, y);
            return r;
        },
        getJw_mm: function (city, x, y, index0, index1) {
            //var index0=0;
            //var index1=1;
            var mappx_src = this.correct_pts[city][index0];
            var gp_src = this.correct_pts[city][index0];
            var dgPix = this.getDgPix_mm(city, index0, index1);

            var px = this.fromMap(city, x, y);
            var px_src = this.fromMap(city, mappx_src.x, mappx_src.y);
            //var dj1=gpsToDegree(gp_src.j),dw1=gpsToDegree(gp_src.w);
            var dj1 = gp_src.utm_x, dw1 = gp_src.utm_y;
            //alert(dgPix.x+',xy,'+dgPix.y);

            var x_1 = px_src.x;
            var y_1 = px_src.y;

            var px_s = px.x - x_1, py_s = y_1 - px.y;
            //alert(dgPix.x+','+dgPix.y);
            var gp_j = px_s / dgPix.x + dj1;
            var gp_w = py_s / dgPix.y + dw1;
            return {lng: gp_j, lat: gp_w};
            //return {j:degreeToGps(gp_j),w:degreeToGps(gp_w)};
        }
        , getOMap_pts: function (city, pts) {
            return this.getOMap_index(city, pts.lng, pts.lat, pts.lt, pts.rb);
        }
        , getMapJw_pts: function (city, pts) {
            return this.getMapJw_index(city, pts.lng, 9998336 - pts.lat, pts.lt, pts.rb);
        }
        , getOMap_index: function (city, utm_x, utm_y, lt, rb) {
            if (!lt || !rb) {
                var index = this.getOMapIndex_mm(city, utm_x, utm_y);
            } else {
                var index = {lt: lt, rb: rb};
            }
            var xy = this.getPx_mm(city, utm_x, utm_y, index.lt, index.rb);
            return {x: Math.floor(xy.x), y: 9998336 - Math.floor(xy.y), lt: index.lt, rb: index.rb};
        }
        , getMapJw_index: function (city, x, y, lt, rb) {
            if (!lt || !rb) {
                var index = this.getLnglatIndex(city, x, y);
            } else {
                var index = {lt: lt, rb: rb};
            }
            var lnglat = this.getJw_mm(city, x, y, index.lt, index.rb);
            return {lng: lnglat.lng, lat: lnglat.lat, lt: index.lt, rb: index.rb};
        }
    });

    var TD = TD || {}

    TD.pointToPixel = function (point, map) {
        var zoom = map.getZoom();
        var center = map.getCenter();
        var size = map.getSize()
        return TD.geo.pointToPixel(point, zoom, center, size)
    }

    TD.geo = {
        pointToPixel: function (point, zoom, center, size) {
            return this.projection.pointToPixel(point, zoom, center, size)
        }

        , pixelToPoint: function (piexl) {

        }
        /**
         * 经纬度变换至墨卡托坐标
         * @param Point 经纬度
         * @return Point 墨卡托
         */
        , lngLatToMercator: function () {
            return this.projection.convertLL2MC(point);
        }
    }
    TD.geo.projection = new MercatorProjection();
    /**
     * 百度墨卡托投影类
     */
    function MercatorProjection() {
    }

    MercatorProjection.prototype = new Projection();
// 静态常量
    TD.extend(MercatorProjection, {
        EARTHRADIUS: 6370996.81,
        MCBAND: [12890594.86, 8362377.87, 5591021, 3481989.83, 1678043.12, 0],
        LLBAND: [75, 60, 45, 30, 15, 0],
        MC2LL: [
            [1.410526172116255e-008, 8.983055096488720e-006, -1.99398338163310, 2.009824383106796e+002, -1.872403703815547e+002, 91.60875166698430, -23.38765649603339, 2.57121317296198, -0.03801003308653, 1.733798120000000e+007],
            [-7.435856389565537e-009, 8.983055097726239e-006, -0.78625201886289, 96.32687599759846, -1.85204757529826, -59.36935905485877, 47.40033549296737, -16.50741931063887, 2.28786674699375, 1.026014486000000e+007],
            [-3.030883460898826e-008, 8.983055099835780e-006, 0.30071316287616, 59.74293618442277, 7.35798407487100, -25.38371002664745, 13.45380521110908, -3.29883767235584, 0.32710905363475, 6.856817370000000e+006],
            [-1.981981304930552e-008, 8.983055099779535e-006, 0.03278182852591, 40.31678527705744, 0.65659298677277, -4.44255534477492, 0.85341911805263, 0.12923347998204, -0.04625736007561, 4.482777060000000e+006],
            [3.091913710684370e-009, 8.983055096812155e-006, 0.00006995724062, 23.10934304144901, -0.00023663490511, -0.63218178102420, -0.00663494467273, 0.03430082397953, -0.00466043876332, 2.555164400000000e+006],
            [2.890871144776878e-009, 8.983055095805407e-006, -0.00000003068298, 7.47137025468032, -0.00000353937994, -0.02145144861037, -0.00001234426596, 0.00010322952773, -0.00000323890364, 8.260885000000000e+005]
        ],
        LL2MC: [
            [-0.00157021024440, 1.113207020616939e+005, 1.704480524535203e+015, -1.033898737604234e+016, 2.611266785660388e+016, -3.514966917665370e+016, 2.659570071840392e+016, -1.072501245418824e+016, 1.800819912950474e+015, 82.5],
            [8.277824516172526e-004, 1.113207020463578e+005, 6.477955746671608e+008, -4.082003173641316e+009, 1.077490566351142e+010, -1.517187553151559e+010, 1.205306533862167e+010, -5.124939663577472e+009, 9.133119359512032e+008, 67.5],
            [0.00337398766765, 1.113207020202162e+005, 4.481351045890365e+006, -2.339375119931662e+007, 7.968221547186455e+007, -1.159649932797253e+008, 9.723671115602145e+007, -4.366194633752821e+007, 8.477230501135234e+006, 52.5],
            [0.00220636496208, 1.113207020209128e+005, 5.175186112841131e+004, 3.796837749470245e+006, 9.920137397791013e+005, -1.221952217112870e+006, 1.340652697009075e+006, -6.209436990984312e+005, 1.444169293806241e+005, 37.5],
            [-3.441963504368392e-004, 1.113207020576856e+005, 2.782353980772752e+002, 2.485758690035394e+006, 6.070750963243378e+003, 5.482118345352118e+004, 9.540606633304236e+003, -2.710553267466450e+003, 1.405483844121726e+003, 22.5],
            [-3.218135878613132e-004, 1.113207020701615e+005, 0.00369383431289, 8.237256402795718e+005, 0.46104986909093, 2.351343141331292e+003, 1.58060784298199, 8.77738589078284, 0.37238884252424, 7.45]
        ]

        /**
         * 根据平面直角坐标计算两点间距离;
         * @param {Point} point1 平面直角点坐标1
         * @param {Point} point2 平面直角点坐标2;
         * @return {Number} 返回两点间的距离
         */
        , getDistanceByMC: function (point1, point2) {
            if (!point1 || !point2) return 0;
            var x1, y1, x2, y2;
            point1 = this.convertMC2LL(point1);
            if (!point1) return 0;
            x1 = this.toRadians(point1.lng);
            y1 = this.toRadians(point1.lat);
            point2 = this.convertMC2LL(point2);
            if (!point2) return 0;
            x2 = this.toRadians(point2.lng);
            y2 = this.toRadians(point2.lat);
            return this.getDistance(x1, x2, y1, y2);
        }
        /**
         * 根据经纬度坐标计算两点间距离;
         * @param {Point} point1 经纬度点坐标1
         * @param {Point} point2 经纬度点坐标2;
         * @return {Number} 返回两点间的距离
         */
        , getDistanceByLL: function (point1, point2) {
            if (!point1 || !point2) return 0;
            point1.lng = this.getLoop(point1.lng, -180, 180);
            point1.lat = this.getRange(point1.lat, -74, 74);
            point2.lng = this.getLoop(point2.lng, -180, 180);
            point2.lat = this.getRange(point2.lat, -74, 74);
            var x1, x2, y1, y2;
            x1 = this.toRadians(point1.lng);
            y1 = this.toRadians(point1.lat);
            x2 = this.toRadians(point2.lng);
            y2 = this.toRadians(point2.lat);
            return this.getDistance(x1, x2, y1, y2);
        }
        /**
         * 平面直角坐标转换成经纬度坐标;
         * @param {Point} point 平面直角坐标
         * @return {Point} 返回经纬度坐标
         */
        , convertMC2LL: function (point) {
            var temp, factor;
            temp = new Point(Math.abs(point.lng), Math.abs(point.lat));
            for (var i = 0; i < this.MCBAND.length; i++) {
                if (temp.lat >= this.MCBAND[i]) {
                    factor = this.MC2LL[i];
                    break;
                }
            }
            ;
            var lnglat = this.convertor(point, factor);
            var point = new Point(lnglat.lng.toFixed(6), lnglat.lat.toFixed(6));
            return point;
        }

        /**
         * 经纬度坐标转换成平面直角坐标;
         * @param {Point} point 经纬度坐标
         * @return {Point} 返回平面直角坐标
         */
        , convertLL2MC: function (point) {
            var temp, factor;
            point.lng = this.getLoop(point.lng, -180, 180);
            point.lat = this.getRange(point.lat, -74, 74);
            temp = new Point(point.lng, point.lat);
            for (var i = 0; i < this.LLBAND.length; i++) {
                if (temp.lat >= this.LLBAND[i]) {
                    factor = this.LL2MC[i];
                    break;
                }
            }
            if (!factor) {
                for (var i = this.LLBAND.length - 1; i >= 0; i--) {
                    if (temp.lat <= -this.LLBAND[i]) {
                        factor = this.LL2MC[i];
                        break;
                    }
                }
            }
            var mc = this.convertor(point, factor);
            var point = new Point(mc.lng.toFixed(2), mc.lat.toFixed(2));
            return point;
        }
        , convertor: function (fromPoint, factor) {
            if (!fromPoint || !factor) {
                return;
            }
            var x = factor[0] + factor[1] * Math.abs(fromPoint.lng);
            var temp = Math.abs(fromPoint.lat) / factor[9];
            var y = factor[2] +
                factor[3] * temp +
                factor[4] * temp * temp +
                factor[5] * temp * temp * temp +
                factor[6] * temp * temp * temp * temp +
                factor[7] * temp * temp * temp * temp * temp +
                factor[8] * temp * temp * temp * temp * temp * temp;
            x *= (fromPoint.lng < 0 ? -1 : 1);
            y *= (fromPoint.lat < 0 ? -1 : 1);
            return new Point(x, y);
        }

        , getDistance: function (x1, x2, y1, y2) {
            return this.EARTHRADIUS * Math.acos((Math.sin(y1) * Math.sin(y2) + Math.cos(y1) * Math.cos(y2) * Math.cos(x2 - x1)));
        }

        , toRadians: function (angdeg) {
            return Math.PI * angdeg / 180;
        }

        , toDegrees: function (angrad) {
            return (180 * angrad) / Math.PI;
        }
        , getRange: function (v, a, b) {
            if (a != null) {
                v = Math.max(v, a);
            }
            if (b != null) {
                v = Math.min(v, b);
            }
            return v
        }
        , getLoop: function (v, a, b) {
            while (v > b) {
                v -= b - a
            }
            while (v < a) {
                v += b - a
            }
            return v;
        }
    });

    TD.extend(MercatorProjection.prototype, {
        /**
         * 经纬度变换至墨卡托坐标
         * @param Point 经纬度
         * @return Point 墨卡托
         */
        lngLatToMercator: function (point) {
            return MercatorProjection.convertLL2MC(point);
        },
        /**
         * 球面到平面坐标
         * @param Point 球面坐标
         * @return Pixel 平面坐标
         */
        lngLatToPoint: function (point) {
            var mercator = MercatorProjection.convertLL2MC(point);
            return new Pixel(mercator.lng, mercator.lat);
        },
        /**
         * 墨卡托变换至经纬度
         * @param Point 墨卡托
         * @returns Point 经纬度
         */
        mercatorToLngLat: function (point) {
            return MercatorProjection.convertMC2LL(point);
        },
        /**
         * 平面到球面坐标
         * @param Pixel 平面坐标
         * @returns Point 球面坐标
         */
        pointToLngLat: function (point) {
            var mercator = new Point(point.x, point.y);
            return MercatorProjection.convertMC2LL(mercator);
        },
        /**
         * 地理坐标转换至像素坐标
         * @param Point 地理坐标
         * @param Number 级别
         * @param Point 地图中心点，注意为了保证没有误差，这里需要传递墨卡托坐标
         * @param Size 地图容器大小
         * @return Pixel 像素坐标
         */
        pointToPixel: function (point, zoom, mapCenter, mapSize, curCity) {
            if (!point) {
                return;
            }
            point = this.lngLatToMercator(point, curCity);
            mapCenter = this.lngLatToMercator(mapCenter)
            var zoomUnits = this.getZoomUnits(zoom);
            var x = Math.round((point.lng - mapCenter.lng) / zoomUnits + mapSize.width / 2);
            var y = Math.round((mapCenter.lat - point.lat) / zoomUnits + mapSize.height / 2);
            return new Pixel(x, y);
        },
        /**
         * 像素坐标转换至地理坐标
         * @param Pixel 像素坐标
         * @param Number 级别
         * @param Point 地图中心点，注意为了保证没有误差，这里需要传递墨卡托坐标
         * @param Size 地图容器大小
         * @return Point 地理坐标
         */
        pixelToPoint: function (pixel, zoom, mapCenter, mapSize, curCity) {
            if (!pixel) {
                return;
            }
            var zoomUnits = this.getZoomUnits(zoom);
            var lng = mapCenter.lng + zoomUnits * (pixel.x - mapSize.width / 2);
            var lat = mapCenter.lat - zoomUnits * (pixel.y - mapSize.height / 2);
            var point = new Point(lng, lat);
            return this.mercatorToLngLat(point, curCity);
        },
        getZoomUnits: function (zoom) {
            return Math.pow(2, (18 - zoom));
        }
    });
    /**
     * 透视图投影
     */
    function PerspectiveProjection() {

    }

    PerspectiveProjection.prototype = new MercatorProjection();
    TD.extend(PerspectiveProjection.prototype, {
        lngLatToMercator: function (lngLat, mapCity) {
            return this._convert2DTo3D(mapCity, MercatorProjection.convertLL2MC(lngLat));
        }
        , mercatorToLngLat: function (mercator, mapCity) {
            return MercatorProjection.convertMC2LL(this._convert3DTo2D(mapCity, mercator));
        }
        , lngLatToPoint: function (lngLat, mapCity) {
            var mercator = this._convert2DTo3D(mapCity, MercatorProjection.convertLL2MC(lngLat));
            return new Pixel(mercator.lng, mercator.lat);
        }
        , pointToLngLat: function (point, mapCity) {
            var mercator = new Point(point.x, point.y);
            return MercatorProjection.convertMC2LL(this._convert3DTo2D(mapCity, mercator));
        }
        , _convert2DTo3D: function (city, point) {
            var p = CoordTrans.getOMap_pts(city || 'bj', point);
            return new Point(p.x, p.y);
        }
        , _convert3DTo2D: function (city, point) {
            var p = CoordTrans.getMapJw_pts(city || 'bj', point);
            return new Point(p.lng, p.lat);
        }
        , getZoomUnits: function (zoom) {
            return Math.pow(2, (20 - zoom));
        }
    });

    /**
     * @fileoverview 关于像素坐标类文件.
     *
     * @author yangxinming
     * @version 1.0
     */

//Include("BMap.baidu.lang.Class");

    /**
     * 以像素坐标表示的地图上的一点
     * @param {Number} x 屏幕像素坐标x
     * @param {Number} y 屏幕像素坐标y
     */
    function Pixel(x, y) {
        this.x = x || 0;
        this.y = y || 0;
    };

    Pixel.prototype.equals = function (other) {
        return other && other.x == this.x && other.y == this.y;
    }
    /**
     * @fileoverview 关于地理点坐标类文件.
     *
     * @author yangxinming
     * @version 1.0
     */

//Include("BMap.baidu.lang.Class");


    /**
     * 基本点类,代表地理点坐标;
     * 坐标支持base64编码
     * @param {Object} lng 墨卡托X(经度).
     * @param {Object} lat 墨卡托Y(纬度);.
     * @return {Point} 返回一个地理点坐标对象.
     */
    function Point(lng, lat) {
        // 新增base64支持 - by jz
        if (isNaN(lng)) {
            lng = decode64(lng);
            lng = isNaN(lng) ? 0 : lng;
        }
        if (isString(lng)) {
            lng = parseFloat(lng);
        }
        if (isNaN(lat)) {
            lat = decode64(lat);
            lat = isNaN(lat) ? 0 : lat;
        }
        if (isString(lat)) {
            lat = parseFloat(lat);
        }
        this.lng = lng;
        this.lat = lat;
    }

    Point.isInRange = function (pt) {
        return pt && pt.lng <= 180 && pt.lng >= -180 && pt.lat <= 74 && pt.lat >= -74;
    }
    Point.prototype.equals = function (other) {
        return other && this.lat == other.lat && this.lng == other.lng;
    };

    /**
     * 投影基类，抽象类不可实例化
     * @constructor
     */
    function Projection() {
    };

    /**
     * 抽象，从球面坐标转换到平面坐标
     */
    Projection.prototype.lngLatToPoint = function () {
        throw "lngLatToPoint方法未实现";
    };

    /**
     * 抽象，从平面坐标转换到球面坐标
     */
    Projection.prototype.pointToLngLat = function () {
        throw "pointToLngLat方法未实现";
    };


    var MapStyle = {
        blueness:  //蓝色
            [
                {
                    featureType: 'water',
                    elementType: 'all',
                    stylers: {
                        color: '#044161'
                    }
                }, {
                featureType: 'land',
                elementType: 'all',
                stylers: {
                    color: '#091934'
                }
            }, {
                featureType: 'boundary',
                elementType: 'geometry',
                stylers: {
                    color: '#064f85'
                }
            }, {
                featureType: 'railway',
                elementType: 'all',
                stylers: {
                    visibility: 'off'
                }
            }, {
                featureType: 'highway',
                elementType: 'geometry',
                stylers: {
                    color: '#004981'
                }
            }, {
                featureType: 'highway',
                elementType: 'geometry.fill',
                stylers: {
                    color: '#005b96',
                    lightness: 1
                }
            }, {
                featureType: 'highway',
                elementType: 'labels',
                stylers: {
                    visibility: 'on'
                }
            }, {
                featureType: 'arterial',
                elementType: 'geometry',
                stylers: {
                    color: '#004981',
                    lightness: -39
                }
            }, {
                featureType: 'arterial',
                elementType: 'geometry.fill',
                stylers: {
                    color: '#00508b'
                }
            }, {
                featureType: 'poi',
                elementType: 'all',
                stylers: {
                    visibility: 'off'
                }
            }, {
                featureType: 'green',
                elementType: 'all',
                stylers: {
                    color: '#056197',
                    visibility: 'off'
                }
            }, {
                featureType: 'subway',
                elementType: 'all',
                stylers: {
                    visibility: 'off'
                }
            }, {
                featureType: 'manmade',
                elementType: 'all',
                stylers: {
                    visibility: 'off'
                }
            }, {
                featureType: 'local',
                elementType: 'all',
                stylers: {
                    visibility: 'off'
                }
            }, {
                featureType: 'arterial',
                elementType: 'labels',
                stylers: {
                    visibility: 'off'
                }
            }, {
                featureType: 'boundary',
                elementType: 'geometry.fill',
                stylers: {
                    color: '#029fd4'
                }
            }, {
                featureType: 'building',
                elementType: 'all',
                stylers: {
                    color: '#1a5787'
                }
            }, {
                featureType: 'label',
                elementType: 'all',
                stylers: {
                    visibility: 'off'
                }
            }, {
                featureType: 'poi',
                elementType: 'labels.text.fill',
                stylers: {
                    color: '#ffffff'
                }
            }, {
                featureType: 'poi',
                elementType: 'labels.text.stroke',
                stylers: {
                    color: '#1e1c1c'
                }
            }]
    };

    /**
     * 圆球
     * @param {Object} ctx
     * @param {Object} opts {radius:radius, fillStyle:'#FF0000'}
     */

    function Circle(ctx, opts) {
        DrawElement.call(this, arguments);
        this.context = ctx;
        this.radius = 10;
    }

    Circle.prototype = new DrawElement();
    TD.extend(Circle.prototype, {
        setContext: function (ctx) {
            this.context = ctx;
        },
        draw: function (pixels, drawOptions, margin) {

            for (var i = 0, len = pixels.length; i < len; i++) {
                var pixel = pixels[i];
                var size = typeof drawOptions.size === 'function' ? drawOptions.size(pixel.count) : drawOptions.size;
                var lineWidth = typeof drawOptions.lineWidth === "function" ? drawOptions.lineWidth(pixel.count) : drawOptions.lineWidth;
                var fillStyle = typeof drawOptions.fillStyle === "function" ? drawOptions.fillStyle(pixel.count) : drawOptions.fillStyle;
                var strokeStyle = typeof drawOptions.strokeStyle === "function" ? drawOptions.strokeStyle(pixel.count) : drawOptions.strokeStyle;
                this.drawCircle(pixel.x + margin, pixel.y + margin, size, fillStyle, lineWidth, strokeStyle);

            }
        },
        drawCircle: function (x, y, radius, color, lineWidth, strokeStyle) {
            var ctx = this.context;
            radius = radius || 10;
            ctx.beginPath();
            ctx.fillStyle = color;
            ctx.arc(x, y, radius, 0, 2 * Math.PI, true);
            ctx.fill();
            if (lineWidth) {
                ctx.lineWidth = lineWidth;
                if (strokeStyle) {
                    ctx.strokeStyle = strokeStyle;
                }
                ctx.stroke();
            }
        }
    })

    function DrawElement(ctx) {
        this.ctx = ctx;
    }

    TD.extend(DrawElement.prototype, {})

    /**
     * 渐变圆
     * @param {object} container
     * @param {Object} ctx
     * @param {Object} opts
     */
    function GradientCircle(container, ctx, opts) {
        DrawElement.call(this, arguments);
        this.container = container;
        this.context = ctx;
        this.opts = opts;
    }

    GradientCircle.prototype = new DrawElement();
    TD.extend(GradientCircle.prototype, {
        setContext: function (ctx) {
            this.context = ctx;
        },
        drawPoint: function (x, y, radius, opacity) {
            var ctx = this.context;

            ctx.beginPath();
            var gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
            gradient.addColorStop(0, 'rgba(0,0,0,1)');
            gradient.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = gradient;
            ctx.arc(x, y, radius, 0, Math.PI * 2, true);
            ctx.closePath();
            ctx.fill();
            ctx.globalAlpha = opacity;

            //var canvas_point = this.getPointTmpl(radius);
            //ctx.globalAlpha = opacity;
            //ctx.drawImage(canvas_point, x, y);
        },
        // 绘制单位图形
        //getPointTmpl: function(radius) {
        //	var shape = this.opts.shape;
        //	var tplCanvas = document.createElement('canvas');
        //	var tplCtx = tplCanvas.getContext('2d');
        //	var x = radius;
        //	var y = radius;
        //
        //	//if (shape == 'circle') {
        //	//	tplCanvas.width = tplCanvas.height = radius * 2;
        //	//} else if (shape == 'rect') {
        //	//	tplCanvas.width = tplCanvas.height = radius;
        //	//}
        //
        //	tplCanvas.width = tplCanvas.height = radius * 2;
        //	//tplCtx.beginPath();
        //	var gradient = tplCtx.createRadialGradient(x, y, 0, x, y, radius);
        //	gradient.addColorStop(0, 'rgba(0,0,0,1)');
        //	gradient.addColorStop(1, 'rgba(0,0,0,0)');
        //	tplCtx.fillStyle = gradient;
        //	tplCtx.arc(radius, radius, radius, 0, Math.PI * 2, true);
        //	//tplCtx.closePath();
        //	tplCtx.fill();
        //	// 画不同形状
        //
        //	//tplCtx.beginPath();
        //   //
        //	//if (shape == 'circle') {
        //	//	var gradient = tplCtx.createRadialGradient(x, y, 0, x, y, radius);
        //	//	gradient.addColorStop(0, 'rgba(0,0,0,1)');
        //	//	gradient.addColorStop(1, 'rgba(0,0,0,0)');
        //	//	tplCtx.fillStyle = gradient;
        //	//	tplCtx.arc(radius, radius, radius, 0, Math.PI * 2, true);
        //	//} else if (shape == 'rect') {
        //	//	tplCtx.fillStyle = 'rgba(0,0,0,1)';
        //	//	tplCtx.fillRect(0, 0, radius, radius);
        //	//}
        //   //
        //	//tplCtx.closePath();
        //	//tplCtx.fill();
        //	return tplCanvas;
        //},
        // 调色板
        getColorPaint: function () {
            if (this._colorPaint) {
                // 暂时不缓存
                //return this._colorPaint;
            }
            var gradientConfig = this.opts.gradient;
            var paletteCanvas = document.createElement('canvas');
            var paletteCtx = paletteCanvas.getContext('2d');

            paletteCanvas.width = 256;
            paletteCanvas.height = 1;

            var gradient = paletteCtx.createLinearGradient(0, 0, 256, 1);
            for (var key in gradientConfig) {
                gradient.addColorStop(key, gradientConfig[key]);
            }

            paletteCtx.fillStyle = gradient;
            paletteCtx.fillRect(0, 0, 256, 1);

            this._colorPaint = paletteCtx.getImageData(0, 0, 256, 1).data;
            return this._colorPaint;
        },
        drawColor: function () {
            var palette = this.getColorPaint();
            var ctx = this.context;
            var container = this.container;
            var img = ctx.getImageData(0, 0, container.width, container.height);
            var imgData = img.data;
            var len = imgData.length;
            var max_opacity = this.opts.maxOpacity * 255;
            var min_opacity = this.opts.minOpacity * 255;
            //权重区间
            var max_scope = (this.opts.maxScope > 1 ? 1 : this.opts.maxScope) * 255;
            var min_scope = (this.opts.minScope < 0 ? 0 : this.opts.minScope) * 255;

            if (this.opts.type === 'circle') {    // 普通热力图
                for (var i = 3; i < len; i += 4) {
                    var alpha = imgData[i];

                    var offset = alpha * 4;

                    if (!offset) {
                        continue;
                    }

                    imgData[i - 3] = palette[offset];
                    imgData[i - 2] = palette[offset + 1];
                    imgData[i - 1] = palette[offset + 2];

                    // 范围区间
                    if (imgData[i] > max_scope) {
                        imgData[i] = 0;
                    }
                    if (imgData[i] < min_scope) {
                        imgData[i] = 0;
                    }

                    // 透明度
                    if (imgData[i] > max_opacity) {
                        imgData[i] = max_opacity;
                    }
                    if (imgData[i] < min_opacity) {
                        imgData[i] = min_opacity;
                    }
                }
            } else if (this.opts.type === 'rec') {    // 马赛克热力图
                var w = container.width;

                // 第一次遍历:上色,并过滤不需要的点
                for (var i = 3, j = 1; i < len; i += 4, j++) {
                    var alpha = imgData[i];

                    var offset = alpha * 4;

                    if (!offset) {
                        continue;
                    }

                    imgData[i - 3] = palette[offset];
                    imgData[i - 2] = palette[offset + 1];
                    imgData[i - 1] = palette[offset + 2];

                    /***暂不支持
                     // 范围区间
                     if (imgData[i] > max_scope) {
					imgData[i] = 0;
				}
                     if (imgData[i] < min_scope) {
					imgData[i] = 0;
				}

                     // 透明度
                     if (imgData[i] > max_opacity) {
					imgData[i] = max_opacity;
				}
                     if (imgData[i] < min_opacity) {
					imgData[i] = min_opacity;
				}
                     ***/

                    // 下面这个判断,是找出符合要求的点,把不符合要求的点干掉
                    if (((i - 3) % 20 == 0) && (((i - 3) - (j % w - 1) * 4) % (w * 4 * 6) == 0)) {
                        imgData[i] = 255;
                    } else {
                        imgData[i] = 0;
                    }
                }

                // 第二次比遍历:画格子
                for (var i = 3, j = 1; i < len; i += 4, j++) {
                    if (((i - 3) % 20 == 0) && (((i - 3) - (j % w - 1) * 4) % (w * 4 * 6) == 0)) {
                        var r = imgData[i - 3];
                        var g = imgData[i - 2];
                        var b = imgData[i - 1];

                        var border_color = 40;
                        //var opacity = 255;

                        if (!imgData[i]) {
                            continue;
                        }

                        for (var k = 0; k < 6; k++) {
                            if (k == 5) {
                                var r2 = border_color;
                                var g2 = border_color;
                                var b2 = border_color;
                            } else {
                                var r2 = r;
                                var g2 = g;
                                var b2 = b;
                            }

                            imgData[(i - 3) + (w * 4 * k)] = r2;
                            imgData[(i + 1) + (w * 4 * k)] = r2;
                            imgData[(i + 5) + (w * 4 * k)] = r2;
                            imgData[(i + 9) + (w * 4 * k)] = r2;

                            imgData[(i - 2) + (w * 4 * k)] = g2;
                            imgData[(i + 2) + (w * 4 * k)] = g2;
                            imgData[(i + 6) + (w * 4 * k)] = g2;
                            imgData[(i + 10) + (w * 4 * k)] = g2;

                            imgData[(i - 1) + (w * 4 * k)] = b2;
                            imgData[(i + 3) + (w * 4 * k)] = b2;
                            imgData[(i + 7) + (w * 4 * k)] = b2;
                            imgData[(i + 11) + (w * 4 * k)] = b2;

                            imgData[(i + 13) + (w * 4 * k)] = border_color;
                            imgData[(i + 14) + (w * 4 * k)] = border_color;
                            imgData[(i + 15) + (w * 4 * k)] = border_color;

                            imgData[(i) + (w * 4 * k)] = 255;
                            imgData[(i + 4) + (w * 4 * k)] = 255;
                            imgData[(i + 8) + (w * 4 * k)] = 255;
                            imgData[(i + 12) + (w * 4 * k)] = 255;
                            imgData[(i + 16) + (w * 4 * k)] = 255;
                        }
                    }
                }
            }

            img.data = imgData;

            ctx.putImageData(img, 0, 0, 0, 0, container.width, container.height);
        }
    });

    /**
     * 热力格子
     * @param {object} container
     * @param {Object} ctx
     * @param {Object} opts
     */
    function Gridding(container, ctx, opts) {
        DrawElement.call(this, arguments);
        this.container = container;
        this.context = ctx;
        this.opts = opts;
    }

    Gridding.prototype = new DrawElement();
    TD.extend(Gridding.prototype, {
        setContext: function (ctx) {
            this.context = ctx;
        },
        drawPoint: function (x, y, radius, opacity) {
            var ctx = this.context;

            ctx.beginPath();
            var gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
            gradient.addColorStop(0, 'rgba(0,0,0,1)');
            gradient.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = gradient;
            ctx.arc(x, y, radius, 0, Math.PI * 2, true);
            ctx.closePath();
            ctx.fill();
            ctx.globalAlpha = opacity;

            //var canvas_point = this.getPointTmpl(radius);
            //ctx.globalAlpha = opacity;
            //ctx.drawImage(canvas_point, x, y);
        },
        // 绘制单位图形
        //getPointTmpl: function(radius) {
        //	var shape = this.opts.shape;
        //	var tplCanvas = document.createElement('canvas');
        //	var tplCtx = tplCanvas.getContext('2d');
        //	var x = radius;
        //	var y = radius;
        //
        //	//if (shape == 'circle') {
        //	//	tplCanvas.width = tplCanvas.height = radius * 2;
        //	//} else if (shape == 'rect') {
        //	//	tplCanvas.width = tplCanvas.height = radius;
        //	//}
        //
        //	tplCanvas.width = tplCanvas.height = radius * 2;
        //	//tplCtx.beginPath();
        //	var gradient = tplCtx.createRadialGradient(x, y, 0, x, y, radius);
        //	gradient.addColorStop(0, 'rgba(0,0,0,1)');
        //	gradient.addColorStop(1, 'rgba(0,0,0,0)');
        //	tplCtx.fillStyle = gradient;
        //	tplCtx.arc(radius, radius, radius, 0, Math.PI * 2, true);
        //	//tplCtx.closePath();
        //	tplCtx.fill();
        //	// 画不同形状
        //
        //	//tplCtx.beginPath();
        //   //
        //	//if (shape == 'circle') {
        //	//	var gradient = tplCtx.createRadialGradient(x, y, 0, x, y, radius);
        //	//	gradient.addColorStop(0, 'rgba(0,0,0,1)');
        //	//	gradient.addColorStop(1, 'rgba(0,0,0,0)');
        //	//	tplCtx.fillStyle = gradient;
        //	//	tplCtx.arc(radius, radius, radius, 0, Math.PI * 2, true);
        //	//} else if (shape == 'rect') {
        //	//	tplCtx.fillStyle = 'rgba(0,0,0,1)';
        //	//	tplCtx.fillRect(0, 0, radius, radius);
        //	//}
        //   //
        //	//tplCtx.closePath();
        //	//tplCtx.fill();
        //	return tplCanvas;
        //},
        // 调色板
        getColorPaint: function () {
            if (this._colorPaint) {
                return this._colorPaint;
            }
            var gradientConfig = this.opts.gradient;
            var paletteCanvas = document.createElement('canvas');
            var paletteCtx = paletteCanvas.getContext('2d');

            paletteCanvas.width = 256;
            paletteCanvas.height = 1;

            var gradient = paletteCtx.createLinearGradient(0, 0, 256, 1);
            for (var key in gradientConfig) {
                gradient.addColorStop(key, gradientConfig[key]);
            }

            paletteCtx.fillStyle = gradient;
            paletteCtx.fillRect(0, 0, 256, 1);

            this._colorPaint = paletteCtx.getImageData(0, 0, 256, 1).data;
            return this._colorPaint;
        },
        drawColor: function () {
            var palette = this.getColorPaint();
            var ctx = this.context;
            var container = this.container;
            var img = ctx.getImageData(0, 0, container.width, container.height);
            var imgData = img.data;
            var len = imgData.length;
            var max_opacity = this.opts.maxOpacity * 255;
            var min_opacity = this.opts.minOpacity * 255;
            //权重区间
            var max_scope = (this.opts.maxScope > 1 ? 1 : this.opts.maxScope) * 255;
            var min_scope = (this.opts.minScope < 0 ? 0 : this.opts.minScope) * 255;

            var row = len / container.height;

            var j = 1, rowIndex = 1;
            for (var i = 3; i < len; i += 4) {

                if (i < rowIndex * row) {
                    if (i == 3) {
                        imgData[i - 3] = 255;
                        imgData[i - 2] = 255;
                        imgData[i - 1] = 255;
                        imgData[i] = 255;
                    }
                    if (j % 8 === 0 || rowIndex % 8 == 0) {

                    } else {
                        imgData[i - 3] = 255;
                        imgData[i - 2] = 255;
                        imgData[i - 1] = 255;
                        imgData[i] = 255 * 0.1;
                    }
                    j++;
                } else {
                    rowIndex++;
                    j = 1;

                    imgData[i - 3] = 255;
                    imgData[i - 2] = 255;
                    imgData[i - 1] = 255;
                    imgData[i] = 255 * 0.1;

                    j++;
                }


            }
            img.data = imgData;

            ctx.putImageData(img, 0, 0, 0, 0, container.width, container.height);
        }
    });

    /**
     * 热力方格
     *
     */
    function HeatSquare(container, ctx, opts) {
        DrawElement.call(this, arguments);
        this.container = container;
        this.context = ctx;
        this.opts = opts;
    }

    HeatSquare.prototype = new DrawElement();
    TD.extend(HeatSquare.prototype, {
        setContext: function (ctx) {
            this.context = ctx;
        },
        drawPoint: function (x, y, width, opacity) {
            var ctx = this.context;
            var canvas_point = this.getPointTmpl(width);
            ctx.globalAlpha = opacity;
            ctx.drawImage(canvas_point, x, y);
        },
        // 绘制单位方格
        getPointTmpl: function (width) {
            var tplCanvas = document.createElement('canvas');
            var tplCtx = tplCanvas.getContext('2d');
            var x = 0;
            var y = 0;

            tplCanvas.width = tplCanvas.height = width * 1;

            tplCtx.fillStyle = '#000000';
            tplCtx.fillRect(x, y, tplCanvas.width, tplCanvas.height);

            return tplCanvas;
        },
        // 调色板
        getColorPaint: function () {
            var gradientConfig = this.opts.gradient;
            var paletteCanvas = document.createElement('canvas');
            var paletteCtx = paletteCanvas.getContext('2d');

            paletteCanvas.width = 256;
            paletteCanvas.height = 1;

            var gradient = paletteCtx.createLinearGradient(0, 0, 256, 1);
            for (var key in gradientConfig) {
                gradient.addColorStop(key, gradientConfig[key]);
            }

            paletteCtx.fillStyle = gradient;
            paletteCtx.fillRect(0, 0, 256, 1);

            return paletteCtx.getImageData(0, 0, 256, 1).data;
        },
        drawColor: function () {
            console.log(111)
            var palette = this.getColorPaint();
            var ctx = this.context;
            var container = this.container;
            var img = ctx.getImageData(0, 0, container.width, container.height);
            var imgData = img.data;
            var len = imgData.length;
            var max_opacity = this.opts.maxOpacity * 255;
            var min_opacity = this.opts.minOpacity * 255;

            var max_scope = (this.opts.maxScope > 1 ? 1 : this.opts.maxScope) * 255;
            var min_scope = (this.opts.minScope < 0 ? 0 : this.opts.minScope) * 255;

            var w = container.width * 4;

            for (var i = 3; i < len; i += 4) {
                var alpha = imgData[i];

                var offset = alpha * 4;

                if (!offset) {
                    continue;
                }

                imgData[i - 3] = palette[offset];
                imgData[i - 2] = palette[offset + 1];
                imgData[i - 1] = palette[offset + 2];
                imgData[i] = 255;


            }
            img.data = imgData;
            ctx.putImageData(img, 0, 0, 0, 0, container.width, container.height);
        }
    });
    /**
     * Created by tendcloud on 2016/1/28.
     */
    /**
     * 图片
     * @param {Object} ctx
     * @param {Object} opts {radius:radius, fillStyle:'#FF0000'}
     */

    function horerImage(id, x, y, width, height) {
        DrawElement.call(this, arguments);
        this.id = id;
        this.x = x;
        this.y = y;
        this.width = width;
        this.heigth = height;


    }

    horerImage.prototype = new DrawElement();
    TD.extend(horerImage.prototype, {
        draw: function (ctx, img) {
            ctx.drawImage(img, this.x, this.y, this.width, this.heigth);
        },
        /*
         *判断点是矩形内
         */
        isMouseOver: function (x, y) {
            return !(x < this.x || x > this.x + this.width || y < this.y || y > this.y + this.heigth);
        }
    });

    /**
     * Created by tendcloud on 2016/1/28.
     */
    /**
     * 圆球
     * @param {Object} ctx
     * @param {Object} opts {radius:radius, fillStyle:'#FF0000'}
     */

    function horerCircle(id, x, y, radius, lineWidth, fillStyle, strokeStyle) {
        DrawElement.call(this, arguments);
        this.id = id;
        this.radius = radius || 10;
        this.x = x;
        this.y = y;
        this.lineWidth = lineWidth || 0;
        this.fillStyle = fillStyle;
        this.strokeStyle = strokeStyle;
    }

    horerCircle.prototype = new DrawElement();
    TD.extend(horerCircle.prototype, {
        draw: function (ctx) {
            ctx.beginPath();
            ctx.fillStyle = this.fillStyle;
            ctx.arc(this.x, this.y, this.radius, 0, 2 * Math.PI, true);
            ctx.fill();
            if (this.lineWidth) {
                ctx.lineWidth = this.lineWidth;
                if (this.strokeStyle) {
                    ctx.strokeStyle = this.strokeStyle;
                }
                ctx.stroke();
            }

        },
        /*
         *判断点是否在圆内
         */
        isMouseOver: function (x1, y1) {
            var a = this.x - x1;
            var b = this.y - y1;
            if ((a * a + b * b) > (this.radius + this.lineWidth) * (this.radius + this.lineWidth)) {
                return false;
            } else {
                return true;
            }
        }
    });

    /**
     * 圆球
     * @param {Object} ctx
     * @param {Object} opts {radius:radius, fillStyle:'#FF0000'}
     */

    function Lamp(ctx, opts) {
        DrawElement.call(this, arguments);
        this.context = ctx;
        this.radius = 10;
        this.overDiv = null;
    }

    Lamp.prototype = new DrawElement();
    TD.extend(Lamp.prototype, {
        setContext: function (ctx) {
            this.context = ctx;
        },
        createDiv: function (map) {
            this.context.canvas.style.zIndex = "6";
            var div = document.createElement("div");
            var style = div.style;
            style.position = "fixed";
            style.width = window.innerWidth * 5 + "px";
            style.height = window.innerWidth * 5 + "px";
            style.backgroundColor = "rgba(0,0,0,0.85)";
            style.top = -window.innerHeight * 2 + "px";
            style.left = -window.innerWidth * 2 + "px";
            style.zIndex = "5";
            map.getPanes().labelPane.appendChild(div);
            this.overDiv = div;
        },
        draw: function (pixels, drawOptions, margin, map) {
            if (this.overDiv === null) {
                this.createDiv(map);
            }

            var size = map.getSize();
            //this.context.fillStyle = "rgba(0, 0, 0, 1)";
            //this.context.fillRect(0, 0, size.width, size.height);

            for (var i = 0, len = pixels.length; i < len; i++) {
                var pixel = pixels[i];
                var size = typeof drawOptions.size === 'function' ? drawOptions.size(point.count) : drawOptions.size;
                this.drawExcircle(pixel.x + margin, pixel.y + margin, size);
            }

            for (var i = 0, len = pixels.length; i < len; i++) {
                var pixel = pixels[i];
                var size = typeof drawOptions.size === 'function' ? drawOptions.size(point.count) : drawOptions.size;
                var lineWidth = typeof drawOptions.lineWidth === "function" ? drawOptions.lineWidth(point.count) : drawOptions.lineWidth;
                var fillStyle = typeof drawOptions.fillStyle === "function" ? drawOptions.fillStyle(point.count) : drawOptions.fillStyle;
                var strokeStyle = typeof drawOptions.strokeStyle === "function" ? drawOptions.strokeStyle(point.count) : drawOptions.strokeStyle;
                this.drawCircle(pixel.x + margin, pixel.y + margin, size, fillStyle, lineWidth, strokeStyle);

            }

        },
        drawExcircle: function (x, y, radius, color) {

            this.context.beginPath();
            var rGrd = this.context.createRadialGradient(x, y, radius, x, y, radius + 15);
            rGrd.addColorStop(0, 'rgba(165, 25, 2, 1)');
            rGrd.addColorStop(1, 'rgba(0, 0, 0, 0.8)');
            this.context.fillStyle = rGrd;
            //this.context.fillStyle = "rgba(226, 17, 12, 1)";
            this.context.arc(x, y, radius + 15, 0, 2 * Math.PI, true);
            this.context.fill();
        },
        drawCircle: function (x, y, radius, color, lineWidth, strokeStyle) {
            this.context.beginPath();
            var rGrd = this.context.createRadialGradient(x, y, 0, x, y, radius);
            rGrd.addColorStop(0, 'rgba(255, 255, 255, 1)');
            rGrd.addColorStop(0.3, 'rgba(255, 255, 255, 1)');

            rGrd.addColorStop(0.4, 'rgba(246, 249, 47, 1)');
            //rGrd.addColorStop(0.6, 'rgba(255, 230, 61, 1)');

            rGrd.addColorStop(0.4, 'rgba(255, 241, 0, 1)');
            rGrd.addColorStop(0.8, 'rgba(255, 241, 0, 1)');

            rGrd.addColorStop(1, 'rgba(226, 17, 12, 1)');
            this.context.fillStyle = rGrd;
            this.context.arc(x, y, radius, 0, 2 * Math.PI, true);
            this.context.fill();


        }
    })

    /**
     * 探针
     *
     */

    function Probe(opts) {
        this.anBorderColor = opts.anBorderColor;//同比边框
        this.anBgColor = opts.anBgColor;//同比背景
        this.anRadius = opts.anRadius;  //同比半径
        this.thanBorderColor = opts.thanBorderColor; //环比边框
        this.thanBgColor = opts.thanBgColor; //环比背景
        this.thanRadius = opts.thanRadius;//环比半径
        this.pixelX = opts.pixelX;
        this.pixelY = opts.pixelY;
        this.ellipseSize = opts.ellipseSize;//椭圆扁扁平系数
        this.img1 = opts.img1;
        this.img2 = opts.img2;
        this.isLoadImg = false;
        this.id = opts.id;

        //头部小标属性
        this.img1Point = {
            x: 0,
            y: 0,
            width: 0,
            height: 0
        };
        //最大圆环属性
        this.maxCirPoint = {
            x: 0,
            y: 0,
            a: 0,
            b: 0
        };
    }

    TD.extend(Probe.prototype, {
        loadImg: function (fun) {
            var me = this;
            if (this.isLoadImg) {
                fun(me.img, me.img2);
            } else {
                var img = new Image();
                img.src = me.imgsrc1;
                img.onload = function () {
                    me.isLoadImg = true;
                    var img2 = new Image();
                    img2.src = me.imgsrc2;

                    img2.onload = function () {
                        me.img = img;
                        me.img2 = img2;
                        fun(me.img, me.img2);
                    }
                }
            }
        },
        draw: function (ctx) {
            var me = this;

            var height = me.img2.height;
            var width = me.img2.width;
            var imgY = me.pixelY - height;
            var imgX = me.pixelX - width / 2;

            ctx.drawImage(me.img2, imgX, imgY);
            me.maxCirPoint = {
                x: me.pixelX,
                y: imgY,
                a: me.anRadius > me.thanRadius ? me.anRadius : me.thanRadius,
                b: (me.anRadius > me.thanRadius ? me.anRadius : me.thanRadius) * me.ellipseSize
            };
            if (me.anRadius > me.thanRadius) {
                me.drawCircle(ctx, me.pixelX, imgY, me.anRadius, me.anRadius * me.ellipseSize, me.anBorderColor, me.anBgColor);
                me.drawCircle(ctx, me.pixelX, imgY, me.thanRadius, me.thanRadius * me.ellipseSize, me.thanBorderColor, me.thanBgColor);

            } else {
                me.drawCircle(ctx, me.pixelX, imgY, me.thanRadius, me.thanRadius * me.ellipseSize, me.thanBorderColor, me.thanBgColor);

                me.drawCircle(ctx, me.pixelX, imgY, me.anRadius, me.anRadius * me.ellipseSize, me.anBorderColor, me.anBgColor);
            }

            me.img1Point = {
                x: imgX,
                y: imgY - me.img1.height,
                width: me.img1.width,
                height: me.img1.height
            };
            ctx.drawImage(me.img1, imgX, me.img1Point.y);

        },
        drawCircle: function (ctx, x, y, a, b, borderColor, bgColor, lineWidth) {

            var step = (a > b) ? 1 / a : 1 / b;
            ctx.beginPath();
            ctx.moveTo(x + a, y);
            for (var i = 0; i < 2 * Math.PI; i += step) {
                ctx.lineTo(x + a * Math.cos(i), y + b * Math.sin(i));
            }
            ctx.closePath();
            ctx.fillStyle = bgColor;
            ctx.fill();
            ctx.strokeStyle = borderColor;
            ctx.lineWidth = lineWidth;
            ctx.stroke();

        },
        /*
         * 是否在环内
         */
        containsRing: function (h, k) {
            return (this.maxCirPoint.x - h) * (this.maxCirPoint.x - h) / (this.maxCirPoint.a * this.maxCirPoint.a) + (this.maxCirPoint.y - k) * (this.maxCirPoint.y - k) / (this.maxCirPoint.b * this.maxCirPoint.b) <= 1;
        },
        /*
         *是否在头部
         */
        containstop: function (x, y) {
            return !(x < this.img1Point.x || x > this.img1Point.x + this.img1Point.width || y < this.img1Point.y || y > this.img1Point.y + this.img1Point.height);
        }


    });

    /**
     * Created by ch on 2015/12/7.
     */
    /**
     * ��Բ
     * @param {Object} ctx
     * @param {Object} opts {radius:radius, fillStyle:'#FF0000'}
     */
    /*define(function(reqire,exports,module){
     function Round(ctx, options){
     this.context = ctx;
     this.o = options;
     }
     Round.prototype = {
     setContext : function(ctx){
     this.context = ctx;
     },
     draw : function(options){
     var ctx = this.context,
     con = options,
     r = (con.xR > con.yR) ? con.xR : con.yR,
     ratioX = con.xR / r,
     ratioY = con.yR / r;

     ctx.beginPath();

     ctx.fillStyle = con.fillStyle;
     ctx.scale(ratioX ,ratioY);
     ctx.arc(con.x, con.y ,r,0, 2*Math.PI );
     ctx.fill();ctx.restore();

     //var a = 10, b = 12, x = 100, y = 50;
     //var r = (a > b) ? a : b,ratioX = a / r,ratioY = b / r;
     //ctx.scale(ratioX ,ratioY);
     //ctx.fillStyle = con.fillStyle;
     //ctx.moveTo((con.x + con.xR) / ratioX, con.y / ratioY);
     //ctx.arc(con.x / ratioX, con.y / ratioY,r,0, 2*Math.PI );
     //ctx.fill();
     //ctx.stroke();
     //ctx.restore();
     }
     };
     module.exports = Round;
     });*/

    /**
     * Created by ch on 2015/12/3.
     */
    /**
     * Բ��
     * @param {Object} ctx
     * @param {Object} opts {radius:radius, fillStyle:'#FF0000'}
     */
    function Round(container, ctx, opts) {
        this.context = ctx;
        this.o = opts;
    }

    Round.inherits(CanvasOverlay, "Round");

    TD.extend(Round.prototype, {
        setContext: function (ctx) {
            this.context = ctx;
        },
        draw: function (opt) {
            var ctx = this.context
                , border = opt.border
                , fill = opt.fill
                , path = opt.path
                ;
            ctx.beginPath();
            if (border && border.size >= 1) {
                ctx.lineWidth = border.size;
                ctx.strokeStyle = border.color;
                ctx.globalAlpha = border.opacity;
                ctx.arc(path.x, path.y, path.radius, 0, 2 * Math.PI, true);
                ctx.stroke();
            }
            if (fill) {
                ctx.globalAlpha = fill.opacity;
                ctx.fillStyle = fill.color;
                ctx.arc(path.x, path.y, path.radius, 0, 2 * Math.PI, true);
                ctx.fill();
            }
            //ctx.stroke()
        }
    });

    /**
     * Created by ch on 2015/12/8.
     */
    /**
     * ��Բ
     * @param {Object} ctx
     * @param {Object} opts {radius:radius, fillStyle:'#FF0000'}
     */

    function Square(container, ctx, opts) {
        this.context = ctx;
        this.o = opts;
    }

    Square.inherits(CanvasOverlay, "Square");

    TD.extend(Square.prototype, {
        setContext: function (ctx) {
            this.context = ctx;
        },
        draw: function (opt) {
            var ctx = this.context
                , border = opt.border
                , size = 0
                , path = opt.path
                , fill = opt.fill
                ;
            ctx.beginPath();
            //����
            if (border && ( size = parseInt(border.size) ) >= 1) {
                console.log(size);
                ctx.lineWidth = size;
                ctx.strokeStyle = border.color;
                var op = parseFloat(border.opacity);
                if (op < 1) {
                    ctx.globalAlpha = op;
                }
                ctx.strokeRect(path.x, path.y, path.width, path.height);
            }
            //����
            if (fill) {
                ctx.globalAlpha = parseFloat(fill.opacity);
                ctx.fillStyle = fill.color;
                ctx.rect(path.x, path.y, path.width, path.height);
                ctx.fill();
            }
        }

    });
    /**
     * Created by ch on 2016/1/5.
     */
    /**
     * Created by ch on 2015/12/8.
     */
    /**
     * 文本
     * @param {Object} ctx
     * @param {Object} opts {radius:radius, fillStyle:'#FF0000'}
     */

    function Text(container, ctx, opts) {
        DrawElement.call(this, arguments);
        this.container = container;
        this.context = ctx;
        this.o = opts;

        //this.context = ctx;
        //this.o = options;
    }

    Text.inherits(CanvasOverlay, "Text");

    TD.extend(Text.prototype, {
        setContext: function (ctx) {
            this.context = ctx;
        },
        draw: function (opt) {
            var ctx = this.context
                , border = opt.border
                , font = opt.font
                , size = 0
                , path = opt.path
                , fill = opt.fill
                ;
            ctx.beginPath();
            //描边
            ctx.font = font.size + "px " + font.style;
            if (border && ( size = parseInt(border.size) ) >= 1) {
                ctx.globalAlpha = parseFloat(border.opacity);
                ctx.strokeStyle = border.color;
                ctx.lineWidth = size;
                ctx.strokeText(path.text, path.x, path.y);
            }
            //填充
            if (fill) {
                ctx.globalAlpha = parseFloat(fill.opacity);
                ctx.fillStyle = fill.color;
                ctx.fillText(path.text, path.x, path.y);
            }
            //ctx.rect(opt.x,opt.y,opt.width,opt.height);
            //ctx.fill();


            //var ctx = this.context;
            //ctx.font = "bold 50px/50px  黑体,arial,sans-serif";
            //var lg = ctx.createLinearGradient(0, 0, 0, 50);
            //lg.addColorStop(0,"#6633ff");
            //lg.addColorStop(0.5,"#66ccff");
            //lg.addColorStop(1,"#6633ff");
            //ctx.fillStyle = lg;
            //ctx.strokeStyle = "#0099ff";
            //ctx.lineWidth = 5;
            //ctx.shadowColor = "#666666";
            //ctx.shadowBlur = 10;
            //ctx.shadowOffsetX = 5;
            //ctx.shadowOffsetY = 5;
            //ctx.strokeText("canvas文字",200,250);
            //ctx.fillText("canvas文字",200,250);
        }

    });
    function CanvasOverlay() {
        TD.BaseClass.call(this);
        this.margin = 0;	//画布margin距离px
        this.ctx = null;	//canvas对象
        this._count = 0;		//消息ID key
        this.eventType = 'moveend'
    }

    CanvasOverlay.inherits(TD.BaseClass, "CanvasOverlay");
    CanvasOverlay.inherits(BMap.Overlay, "CanvasOverlay");
    TD.extend(CanvasOverlay.prototype, {
        initialize: function (map) {
            var me = this;
            this.map = map;
            this.container = document.createElement('canvas');
            this.ctx = this.container.getContext('2d');
            this.container.style.cssText = 'position:absolute;left:0;top:0;__background:#F00';
            map.getPanes().labelPane.appendChild(this.container);
            var size = map.getSize();
            this.container.width = size.width + me.margin * 2;
            this.container.height = size.height + me.margin * 2;
            map.addEventListener('resize', function (event) {
                console.log(me.hashCode, event.type)
                me.setCanvasSize();
                me._draw(me, event);
            });

            map.addEventListener("load", function (e) {
                me._draw(me, e)
            });
            map.addEventListener("moveend", function (e) {
                console.log(me.hashCode, e.type)
                me._draw(me, e);
                me.eventType = e.type
            });
            map.addEventListener("zoomstart", function (e) {
                me.clearCanvas()
            });
            map.addEventListener("zoomend", function (e) {
                me._draw(me, e)
            });
            map.addEventListener("moving", function (e) {
                me.eventType = e.type
            })

            this.setDrawElement();
            this._overlayParentZIndex();
            return this.container;
        }
        , draw: function () {

        }
        , _draw: function (me, event) {
            var me = this || me;
            this.eventType = event.type;
            me.resize();
            if (!me.keysss) {
                //me.canvasResize();
            }
            me.keysss = true;

        }

        , resize: function () {
        }
        , setDrawElement: function () {
        }

        , canvasResize: function (me) {
            //console.log('canvasResize',new Date().getTime())
            var me = this || me;
            var map = this.map;
            var container = this.container;
            var point = map.getCenter();
            var size = map.getSize();
            ///
            var pixel = map.pointToOverlayPixel(point);

            container.style.left = (pixel.x - size.width / 2 - me.margin) + 'px';
            container.style.top = (pixel.y - size.height / 2 - me.margin) + 'px';
        }

        , clearCanvas: function () {
            var size = this.map.getSize();
            this.getContext().clearRect(0, 0, size.width, size.height);//调整画布
        }

        , setCanvasSize: function () {
            var size = this.map.getSize();
            this.container.width = size.width + this.margin * 2;
            this.container.height = size.height + this.margin * 2;
        }
        , getContext: function () {
            return this.ctx;
        }
        /**
         * push消息，
         * @param {string} workerClassPath worker请求的path
         * @param {json} data提交的json数据
         * @param {Function} callback
         */
        , postMessage: function (workerClassPath, data, callback) {
            var map = this.map;
            var center = map.getCenter();
            var size = map.getSize();
            var msgId = this.setMsgId();
            var request = {
                'type': 'web'
                , 'data': data
                , 'hashCode': this.hashCode
                , 'className': this.className
                , 'classPath': workerClassPath
                , 'msgId': msgId
                , 'map': {
                    'center': {lng: center.lng, lat: center.lat}
                    , 'size': {width: size.width, height: size.height}
                    , 'zoom': map.getZoom()
                    , 'margin': this.margin
                }
            };
            TD.workerMrg.postMessage({request: request}, callback);
        }


        , getMsgId: function () {
            return "msgId_" + this._count.toString(36);
        }
        , setMsgId: function () {
            this._count++
            return "msgId_" + (this._count).toString(36);
        }

        , _overlayParentZIndex: function () {
            this.container.parentNode.style.zIndex = 200;
        }

        /**
         * 设置overlay z-index
         */
        , setZIndex: function (zIndex) {
            this.container.style.zIndex = zIndex;
        }

    });
    /*
     * 地图边界绘画
     */
    function BoundaryOverlay(points, opts) {
        CanvasOverlay.call(this, arguments);
        this.points = points;
        this.drawOptions = {
            max: 100,
            label: { // 显示label文字
                show: true, // 是否显示
                font: "11px", // 设置字号
                minZoom: 7, // 最小显示的级别
                fillStyle: 'rgba(255, 255, 255, 1)',
                text: '{@count}'
            },

            bgcolor: [
                "rgba(238,1,3,1)",
                "rgba(244,73,6,1)",
                "rgba(247,139,7,1)",
                "rgba(250,211,8,1)",
                "rgba(216,249,7,1)",
                "rgba(149,253,7,1)",
                "rgba(94,253,6,1)",
                "rgba(32,251,6,1)"
            ],
            strokeStyle: null, //画线的样式
            lineWidth: 0,//画线的宽度

        };


        this.setDrawOptions(opts);
    }

    BoundaryOverlay.inherits(CanvasOverlay, "BoundaryOverlay");

    TD.extend(BoundaryOverlay.prototype, {
        resize: function () {
            this.setPoints();
        },
        getGeoCenter: function (geo) {
            var minX = geo[0][0];
            var minY = geo[0][1];
            var maxX = geo[0][0];
            var maxY = geo[0][1];
            for (var i = 1; i < geo.length; i++) {
                minX = Math.min(minX, geo[i][0]);
                maxX = Math.max(maxX, geo[i][0]);
                minY = Math.min(minY, geo[i][1]);
                maxY = Math.max(maxY, geo[i][1]);
            }
            return [minX + (maxX - minX) / 2, minY + (maxY - minY) / 2];
        },

        _calculatePixel: function _calculatePixel(map, data, margin) {
            for (var j = 0; j < data.length; j++) {
                if (data[j].geo) {
                    var tmp = [];
                    for (var i = 0; i < data[j].geo.length; i++) {
                        var pixel = map.pointToPixel(new BMap.Point(data[j].geo[i][0], data[j].geo[i][1]));
                        tmp.push([pixel.x + margin, pixel.y + margin, parseFloat(data[j].geo[i][2])]);
                    }
                    data[j].pgeo = tmp;
                }
            }

            return data;
        },
        setPoints: function (points) {
            var me = this;
            this.points = points || this.points;
            if (!this.ctx || !this.points) {
                return
            }
            this.ctx.canvas.style.zIndex = "6";
            this.postMessage('BoundaryOverlay.calculatePixel', this.points, function (pixels) {
                if (me.eventType == 'onmoving') {
                    return;
                }

                me.currentItem = null;

                me.drawLine(pixels);
                me.setData(pixels);
            });
        },
        setData: function (pixels) {
            this.data = [];
            for (var i = 0; i < pixels.length; i++) {
                var temp = pixels[i];
                temp.lats = [];
                temp.lngs = [];
                for (var j = 0; j < temp.geo.length; j++) {
                    var arr = temp.pgeo[j];
                    temp.lats.push(arr[0]);
                    temp.lngs.push(arr[1]);
                }

                this.data.push(temp);
            }
        },
        drawLine: function (data) {
            this.canvasResize();
            this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);


            for (var i = 0, len = data.length; i < len; i++) {
                var item = data[i];
                var geo = item.pgeo;
                this.ctx.beginPath();
                this.ctx.moveTo(geo[0][0], geo[0][1]);

                for (var j = 1; j < geo.length; j++) {
                    this.ctx.lineTo(geo[j][0], geo[j][1]);
                }
                this.ctx.closePath();
                var bgColor = null;
                if (this.currentItem == item) {
                    if (this.drawOptions.overColor) {
                        bgColor = this.drawOptions.overColor;
                    } else {
                        if (item.bgColor) {
                            bgColor = item.bgColor;
                        } else {
                            bgColor = typeof this.drawOptions.bgcolor === "function" ? this.drawOptions.bgcolor(item, i) : this.drawOptions.bgcolor;
                            item.bgColor = bgColor;
                        }

                    }
                } else {
                    if (item.bgColor) {
                        bgColor = item.bgColor;
                    } else {
                        bgColor = typeof this.drawOptions.bgcolor === "function" ? this.drawOptions.bgcolor(item, i) : this.drawOptions.bgcolor;
                        item.bgColor = bgColor;
                    }
                }
                this.ctx.fillStyle = bgColor;

                this.ctx.fill();

                if (this.currentItem == item) {
                    if (this.drawOptions.overBordorColor) {
                        this.ctx.strokeStyle = this.drawOptions.overBordorColor;
                    } else {
                        if (this.drawOptions.lineColor) {
                            this.ctx.strokeStyle = this.drawOptions.lineColor;
                        }
                    }

                } else {
                    if (this.drawOptions.lineColor) {
                        this.ctx.strokeStyle = this.drawOptions.lineColor;
                    }
                }

                this.ctx.lineWidth = this.drawOptions.lineWidth || 1;

                this.ctx.stroke();


                var label = this.drawOptions.label, zoom = this.map.getZoom();
                if (label && label.show && (!label.minZoom || label.minZoom && zoom >= label.minZoom)) {
                    if (label.fillStyle) {
                        this.ctx.fillStyle = label.fillStyle;
                    }
                    var center = this.getGeoCenter(geo);
                    var text = label.text,
                        fontsize = label.font.replace('px', ''),
                        d = data[i], re, x, y;
                    for (var k in d) {
                        if (!isString(d[k]) && !isNumber(d[k])) {
                            continue
                        }
                        re = new RegExp('{@' + k + '}', 'gi');
                        text = text.replace(re, d[k]);
                    }
                    x = center[0] - getBlen(text) * fontsize / 4;
                    this.ctx.fillText(text, x, center[1]);
                }
            }

        },
        isPolyContainsPt: function (lat, lng, pointLat, pointLng) {
            var ret = false;
            var latMin = 90.0;
            var latMax = -90.0;
            var lngMin = 180.0;
            var lngMax = -180.0;
            for (var i = 0; i < lat.length; i++) {
                if (lat[i] > latMax) latMax = lat[i];
                if (lat[i] < latMin) latMin = lat[i];
                if (lng[i] > lngMax) lngMax = lng[i];
                if (lng[i] < lngMin) lngMin = lng[i];
            }
            if (!(pointLat < latMin || pointLat > latMax || pointLng < lngMin || pointLng > lngMax)) {

                for (var i = 0; i < lat.length; i++) {
                    var j = (i + 1) % lat.length;
                    if ((lat[i] < pointLat) != (lat[j] < pointLat) && (pointLng < (lng[j] - lng[i]) * (pointLat - lat[i]) / (lat[j] - lat[i]) + lng[i])) {
                        ret = !ret
                    }
                }
            }
            return ret
        },
        setCurrentItem: function (val, index) {
            if (this.currentItem != val) {
                this.data[index] = this.data[this.data.length - 1];
                this.data[this.data.length - 1] = val;
                this.currentItem = val;

                this.drawLine(this.data);
            }

        },
        bindEvent: function () {
            var me = this;
            if (me.drawOptions.onMouseOver) {
                me.map.addEventListener("mousemove", function (event) {
                    if (me.data) {
                        for (var j = 0; j < me.data.length; j++) {
                            var per = me.data[j];
                            if (me.isPolyContainsPt(per.lats, per.lngs, event.pixel.x, event.pixel.y)) {
                                if (me.drawOptions.onMouseOver) {
                                    me.setCurrentItem(per, j);
                                    me.drawOptions.onMouseOver(per, event, true);
                                }

                                break;
                            } else {
                                me.currentItem = null;
                                if (me.drawOptions.onMouseLeave) {
                                    me.drawOptions.onMouseLeave();
                                }
                            }
                        }
                    }
                });
            }
            me.map.addEventListener("movestart", function (event) {
                me.data = null;
                if (me.drawOptions.onMouseLeave) {
                    me.drawOptions.onMouseLeave();
                }
            });
            me.map.addEventListener("zoomstart", function (event) {
                me.data = null;
                if (me.drawOptions.onMouseLeave) {
                    me.drawOptions.onMouseLeave();
                }
            });
        },
        setDrawOptions: function (opts) {
            for (var i in opts) {
                this.drawOptions[i] = opts[i];
            }
        },
        setDrawElement: function () {
            this.bindEvent();
        }
    });
    function DemoOverlay(points, opts) {
        CanvasOverlay.call(this);
        this.points = points;
        this.opts = opts;
        this.drawElement = null;
        this.map = null;

    }

    DemoOverlay.inherits(CanvasOverlay, "DemoOverlay");
    TD.extend(DemoOverlay.prototype, {
        resize: function () {
            this.setPoints();
        }

        , setPoints: function (points) {
            points = points || this.points;
            if (!this.drawElement || !points) {
                return
            }
            this.points = points;
            var ctx = this.getContext(), p, pixel;
            var me = this;

            this.postMessage('TDMap.pointsToPixels', points, function (pixels) {
                var size = map.getSize();
                //清除画布
                me.getContext().clearRect(0, 0, size.width, size.height);
                //调整画布
                me.canvasResize(me);
                for (var i = 0, len = pixels.length; i < len; i++) {
                    //绘制
                    me.drawElement.draw(pixels[i].x + me.margin, pixels[i].y + me.margin, 5, '#FF00FF');
                }
            })
        }

        , setDrawElement: function () {
            this.drawElement = new Circle(this.ctx);
        }


    })

    /**
     * Created by ch on 2016/1/7.
     */
    var DoodleOverlay = function () {
        //this.canvas = {
        //    target : canvas,
        //    ctx : canvas.getContext("2d")
        //};
        this.drawElement = {};
        this.margin = 0;
        this.shapeList = [];//��״�б����棨�������ԣ�
        this.pointData = [];//��γ���껺��
        //this.pixelData = [];//�������껺��
        this.resizeEvent = new TD.BaseEvent("onresize");


    };
    DoodleOverlay.clone = function () {
        var options, key, src, copy, copyType,
            target = arguments[0],
            i = 1,
            length = arguments.length;
        for (; i < length; i++) {
            if ((options = arguments[i]) !== null) {
                for (key in options) {
                    src = target[key];
                    copy = options[key];
                    if (!copy) {
                        target[key] = copy;
                        continue;
                    }
                    //console.log(key,copy);
                    copyType = copy.constructor;
                    if (copyType === Object || copyType === Array) {//����ݹ�
                        var cloneArg;
                        if (copyType === Array) {
                            cloneArg = (src && src.constructor === Array) ? src : [];
                        } else {
                            cloneArg = (src && src.constructor === Object) ? src : {};
                        }
                        target[key] = DoodleOverlay.clone(cloneArg, copy);
                    } else if (copy !== undefined && copy !== null) {
                        target[key] = copy;
                    }
                }
            }
        }
        return target;
    };
    DoodleOverlay._calculate = {
        toPointSquare: function (path, map) {
            var mXY = {
                    x: path.x + path.width
                    , y: path.y + path.height
                }
                , pointPath = this.toPointJson(map, path, mXY)
                ;
            return pointPath;
        }
        , toPointRound: function (path, map) {
            /*var loc = {
             x : path.x
             ,y : path.y
             }
             ,mXY = {
             x : path.x + path.radius
             ,y : path.y + path.radius
             }
             ,pointPath = this.pixelToPoint(loc, map)
             ,pointMy = this.pixelToPoint(mXY, map)
             ;
             pointPath.old = pointMy;*/
            /*var mXY = {
             x : path.x + path.radius
             ,y : path.y + path.radius
             }
             ,pointPath = this.toPointJson(path, mXY, map);
             //console.log("dd",dd)
             //console.log("pointPath",pointPath)
             return pointPath;*/
            var mXY = {
                    x: path.x + path.radius
                    , y: path.y + path.radius
                }
                , pointPath = this.toPointJson(map, path, mXY)
                ;
            return pointPath;
        }
        , toPointText: function (path, map) {
            var pointPath = this.toPointJson(map, path);
            return pointPath;
        }
        , toPixelSquare: function (path, map) {
            /*var loc = {
             lng : path.lng
             ,lat : path.lat
             }
             ,pixelPath = this.pointToPixel(loc, map)
             ,pixelMy = this.pointToPixel(path.old, map)
             ;
             pixelPath.width = pixelMy.x - pixelPath.x;
             pixelPath.height = pixelMy.y - pixelPath.y;
             return pixelPath;*/
            var mePath = this.toPixelJson(map, path)
                , pixel = mePath.bPath;
            pixel.width = mePath.sPath.x - pixel.x;
            pixel.height = mePath.sPath.y - pixel.y;
            return pixel;
        }
        , toPixelRound: function (path, map) {
            /*var loc = {
             lng : path.lng
             ,lat : path.lat
             }
             ,pixelPath = this.pointToPixel(loc, map)
             ,pixelMy = this.pointToPixel(path.old, map)
             ;
             pixelPath.radius = pixelMy.x - pixelPath.x;
             return pixelPath;*/
            var mePath = this.toPixelJson(map, path)
                , pixel = mePath.bPath;
            pixel.radius = mePath.sPath.x - pixel.x;
            return pixel;
        }
        , toPixelText: function (path, map) {
            var mePath = this.toPixelJson(map, path)
                , pixel = mePath.bPath;
            return pixel;
        }
        , toPixelJson: function (map, path) {
            var loc = {
                lng: path.lng
                , lat: path.lat
            }
                , pixelPath = this.pointToPixel(loc, map)
                , obj = {
                bPath: pixelPath
            };
            if (path.old) {
                var pixelSizePath = this.pointToPixel(path.old, map);
                obj.sPath = pixelSizePath;
            }
            return obj
        }
        , toPointJson: function (map, path, old) {
            var loc = {
                    x: path.x
                    , y: path.y
                }
                , pointPath = this.pixelToPoint(loc, map)
                ;
            if (old) {
                var pointMy = this.pixelToPoint(old, map)
                pointPath.old = pointMy;
            }
            return pointPath

        }
        /**
         * ��γ��ת����
         * @param {Object} point
         * @param {Object} map
         */
        , pointToPixel: function (point, map) {
            var zoom = map.zoom;
            var center = map.center;
            var size = map.size;
            var obj = map.pointToPixel(point, zoom, center, size);
            return obj;
        }
        , /**
         * ���ض�ת��γ
         * @param {Object} pixel
         * @param {Object} map
         */
        pixelToPoint: function (pixel, map) {
            var zoom = map.zoom;
            var center = map.center;
            var size = map.size;
            var obj = map.pixelToPoint(pixel, zoom, center, size);
            return obj;
        }
    };
    DoodleOverlay.inherits(CanvasOverlay, "DoodleOverlay");
    TD.extend(DoodleOverlay.prototype, {
        resize: function () {
            this.canvasResize(this);
            this.upShapeList();
        },
        /**
         * ���ӵ�����״
         * @param options
         */
        add: function (options) {
            //console.log("add",options)
            this.shapeList.push(options);
            var path = options.pot.path
                , pointPath = DoodleOverlay._calculate["toPoint" + options.type](path, this.map);
            this.pointData.push(pointPath);
            this.drawShape(options);

        }
        /**
         * ������״ɾ��
         * @param index
         */
        , del: function (index) {
            //this.pixelData.splice(index,1);
            this.pointData.splice(index, 1);
            this.shapeList.splice(index, 1);
            for (var i = 0, len = this.shapeList.length; i < len; i++) {
                this.shapeList[i].index = i;
            }
            this.drawShapeList();
            console.log("del", this.shapeList)
        }
        /**
         * ������״�޸�
         * @param options
         * @param index
         */
        , up: function (options, index) {
            //console.log("up",options)
            this.shapeList[index] = this.shapeList[index] || {};
            if (options) {
                this.shapeList[index] = DoodleOverlay.clone(this.shapeList[index], options);
                var path = options.pot.path
                    , pointPath = DoodleOverlay._calculate["toPoint" + options.type](path, this.map);
                this.pointData[index] = pointPath;

                //this.pixelData[index] = loc;

                /*var path = options.pot.path
                 ,loc = {
                 x : path.x
                 ,y : path.y
                 }
                 ,point = DoodleOverlay._calculate.pixelToPoint(loc, this.map);
                 this.pointData[index] = point;
                 this.pixelData[index] = loc;
                 this.shapeList[index] =  TD.extend(this.shapeList[index],options);*/
            } else {
                this.shapeList[index] = options;
                this.pointData[index] = options;
                //this.pixelData[index] = options;
            }


            this.drawShapeList();
        }
        /**
         * ������״�滭
         * @param options
         */
        , drawShape: function (options) {
            if (!this.drawElement[options.type]) {
                this.setDrawExampale(options.type);
            }
            //console.log(map.overlayPixelToPoint(options.x,options.y));

            this.drawElement[options.type].draw(options.pot);
        }
        /**
         * ������״�ػ�
         */
        , drawShapeList: function () {
            this.ctx.clearRect(0, 0, this.container.width, this.container.height);
            for (var i = 0, gulp = this.shapeList, len = gulp.length; i < len; i++) {
                //console.log("draw",gulp[i])
                if (gulp[i])this.drawShape(gulp[i]);
            }
        }
        /**
         * ���µ�ǰ��ͼ���б�
         * @param gulp
         * @param type �ػ�
         *
         */
        , upShapeList: function (gulp) {
            var list = this.shapeList
                , pointArr = this.pointData
            //,pixelArr = []
                , map = this.map
                ;
            for (var i = 0, len = pointArr.length; i < len; i++) {
                var li = list[i];
                var pixel = DoodleOverlay._calculate["toPixel" + li.type](pointArr[i], map);
                li.pot.path = DoodleOverlay.clone(li.pot.path, pixel);
            }
            this.drawShapeList();
            this.dispatchEvent(this.resizeEvent, {data: DoodleOverlay.clone([], this.shapeList)});
        }
        /**
         * ʵ������״�滭����
         * @param type
         */
        , setDrawExampale: function (type) {
            if (type) {
                switch (type) {
                    case "Text" :
                        this.drawElement[type] = new Text(this.container, this.ctx, {});
                        break;
                    case "Round" :
                        this.drawElement[type] = new Round(this.container, this.ctx, {});
                        break;
                    case "Square" :
                        this.drawElement[type] = new Square(this.container, this.ctx, {});
                        break;
                    default :
                        break;
                }

            }
        }
        , setDrawElement: function () {
            this.container.style.zIndex = "500";
            //this.pixelToPoint
            //this.ctx.canvas.style.background = "rgba(0,0,0,0.5)";

        }
    });

    /**
     * Created by tendcloud on 2016/1/28.
     */
    /*
     * 点的绘制
     */
    function DotDragOverlay(points, opts) {
        CanvasOverlay.call(this, arguments);
        this.points = points;
        this.drawOptions = {
            fillStyle: null, // 填充颜色
            lineWidth: 0,                       // 描边宽度
            shadowColor: null, // 投影颜色
            shadowBlur: 0,                      // 投影模糊级数
            globalCompositeOperation: null, // 颜色叠加方式
            size: 4, // 半径
            draw: Circle  //绘画对象

        };
        this.drawElement = null;
        this.map = null;
        this.setDrawOptions(opts);
        this.drawData = [];
        this.mouse = null;
    }

    DotDragOverlay.inherits(CanvasOverlay, "DotDragOverlay");

    TD.extend(DotDragOverlay.prototype, {
        resize: function () {
            this.setPoints();
        },

        setPoints: function (points) {
            var me = this;
            this.points = points || this.points;

            var pixels = [];

            this.postMessage('HeatOverlay.pointsToPixels', this.points, function (pixels) {
                if (me.eventType == 'onmoving') {
                    return;
                }
                var size = me.map.getSize();
                me.getContext().clearRect(0, 0, size.width, size.height);//调整画布
                me.canvasResize(me);
                me._setCtx();
                me.drawData = [];
                var drawOptions = me.drawOptions;
                for (var i = 0; i < pixels.length; i++) {
                    var pixel = pixels[i];
                    var size = typeof drawOptions.size === 'function' ? drawOptions.size(pixel.count) : drawOptions.size;
                    var lineWidth = typeof drawOptions.lineWidth === "function" ? drawOptions.lineWidth(pixel.count) : drawOptions.lineWidth;
                    var fillStyle = typeof drawOptions.fillStyle === "function" ? drawOptions.fillStyle(pixel.count) : drawOptions.fillStyle;
                    var strokeStyle = typeof drawOptions.strokeStyle === "function" ? drawOptions.strokeStyle(pixel.count) : drawOptions.strokeStyle;
                    var temp = new me.drawOptions.draw(i,
                        pixels[i].x + me.margin,
                        pixels[i].y + me.margin,
                        size,
                        lineWidth,
                        fillStyle,
                        strokeStyle
                    );

                    me.drawData.push(temp);
                }

                for (var j = 0; j < me.drawData.length; j++) {
                    me.drawData[j].draw(me.ctx);
                }

            });

        },
        bingEvent: function () {
            var me = this;
            if (me.drawOptions.onMouseOver) {
                me.map.addEventListener("mousemove", function (event) {

                    for (var j = 0; j < me.drawData.length; j++) {
                        var per = me.drawData[j];
                        if (per.isMouseOver(event.pixel.x, event.pixel.y)) {
                            if (me.drawOptions.onMouseOver) {
                                me.drawOptions.onMouseOver({curr: per, index: j}, event);
                            }
                            break;
                        } else {
                            if (me.drawOptions.onMouseLeave) {
                                me.drawOptions.onMouseLeave();
                            }
                        }
                    }
                }, false);
            }
            if (me.drawOptions.onClick) {
                me.map.addEventListener("click", function (event) {

                    for (var j = 0; j < me.drawData.length; j++) {
                        var per = me.drawData[j];
                        if (per.isMouseOver(event.pixel.x, event.pixel.y)) {
                            if (me.drawOptions.onClick) {
                                me.drawOptions.onClick({curr: per, index: j}, event);
                            }
                            break;
                        } else {
                            if (me.drawOptions.onMouseLeave) {
                                me.drawOptions.onMouseLeave();
                            }
                        }
                    }
                }, false);
            }


        },
        setDrawOptions: function (opts) {
            for (var i in opts) {
                this.drawOptions[i] = opts[i];
            }
        },
        _setCtx: function () {
            if (this.drawOptions.shadowBlur) {
                this.ctx.shadowBlur = this.drawOptions.shadowBlur;
            }
            if (this.drawOptions.shadowColor) {
                this.ctx.shadowColor = this.drawOptions.shadowColor;
            }
            if (this.drawOptions.globalCompositeOperation) {
                this.ctx.globalCompositeOperation = this.drawOptions.globalCompositeOperation;
            }
            if (this.drawOptions.lineWidth) {
                this.ctx.lineWidth = this.drawOptions.lineWidth;
            }
        },
        setDrawElement: function () {
            //this.mouse = captureMouse(this.container);
            this.bingEvent();
        },
        setDraw: function (cir) {

        }
    });
    /*
     * 点的绘制
     */
    function DotOverlay(points, opts) {
        CanvasOverlay.call(this, arguments);
        this.points = points;
        this.drawOptions = {
            fillStyle: null, // 填充颜色
            lineWidth: 0,                       // 描边宽度
            shadowColor: null, // 投影颜色
            shadowBlur: 0,                      // 投影模糊级数
            globalCompositeOperation: null, // 颜色叠加方式
            size: 4, // 半径
            draw: Circle  //绘画对象

        };
        this.drawElement = null;
        this.map = null;
        this.setDrawOptions(opts);
    }

    DotOverlay.inherits(CanvasOverlay, "DotOverlay");

    TD.extend(DotOverlay.prototype, {
        resize: function () {
            this.setPoints();
        },

        setPoints: function (points) {
            var me = this;
            this.points = points || this.points;
            if (!this.drawElement || !this.points) {
                return
            }

            var pixels = [];

            this.postMessage('HeatOverlay.pointsToPixels', this.points, function (pixels) {
                if (me.eventType == 'onmoving') {
                    return
                }
                ;
                var size = me.map.getSize();
                me.getContext().clearRect(0, 0, size.width, size.height);//调整画布
                me.canvasResize(me);

                me._setCtx();

                me.drawElement.draw(pixels, me.drawOptions, me.margin, me.map)
            });

        },

        setDrawOptions: function (opts) {
            for (var i in opts) {
                this.drawOptions[i] = opts[i];
            }
        },
        _setCtx: function () {
            if (this.drawOptions.shadowBlur) {
                this.ctx.shadowBlur = this.drawOptions.shadowBlur;
            }
            if (this.drawOptions.shadowColor) {
                this.ctx.shadowColor = this.drawOptions.shadowColor;
            }
            if (this.drawOptions.globalCompositeOperation) {
                this.ctx.globalCompositeOperation = this.drawOptions.globalCompositeOperation;
            }
            if (this.drawOptions.lineWidth) {
                this.ctx.lineWidth = this.drawOptions.lineWidth;
            }
        },
        setDrawElement: function () {
            this.drawElement = new this.drawOptions.draw(this.ctx);
        },
        setDraw: function (cir) {
            this.drawElement = new cir(this.ctx);
        }
    });
    /*
     * 网格聚合网络
     */
    function GriddingOverlay(points, opts) {
        CanvasOverlay.call(this, arguments);
        this.points = points;
        this.drawOptions = { // 绘制参数
            size: 50, // 网格大小
            opacity: '0.5',
            label: { // 是否显示文字标签
                show: true,
            },
            gradient: { // 显示的颜色渐变范围
                '0': 'blue',
                '0.6': 'cyan',
                '0.7': 'lime',
                '0.8': 'yellow',
                '1.0': 'red'
            },
            type: "sum", //sum 聚合权重累加  聚合权重平均
            padding: 0
        }
        this._grad = null;
        this.setDrawOptions(opts);
        this._generalGradient(this.drawOptions.gradient);

    }

    GriddingOverlay.inherits(CanvasOverlay, "GriddingOverlay");

    TD.extend(GriddingOverlay.prototype, {
        resize: function () {
            this.setPoints();
        },
        _generalGradient: function (grad) {
            // create a 256x1 gradient that we'll use to turn a grayscale heatmap into a colored one
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');
            var gradient = ctx.createLinearGradient(0, 0, 0, 256);

            canvas.width = 1;
            canvas.height = 256;

            for (var i in grad) {
                gradient.addColorStop(i, grad[i]);
            }

            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, 1, 256);

            this._grad = ctx.getImageData(0, 0, 1, 256).data;
        },
        _getColorByGradient: function (count, max, opacity) {
            var maxF = max || 10;

            var index = count / maxF;
            if (index > 1) {
                index = 1;
            }
            index *= 255;
            index = parseInt(index, 10);
            index *= 4;

            var color = 'rgba(' + this._grad[index] + ', ' + this._grad[index + 1] + ', ' + this._grad[index + 2] + ', ' + (opacity || 0) + ')';
            return color;
        },
        setPoints: function (points) {
            var me = this;
            me.points = points || me.points;
            if (!me.ctx || !me.points) {
                return
            }


            var zoom = me.map.getZoom();
            var zoomUnit = Math.pow(2, 18 - zoom);
            var mercatorProjection = me.map.getMapType().getProjection();
            var mcCenter = mercatorProjection.lngLatToPoint(me.map.getCenter());
            var size = this.drawOptions.size * zoomUnit;
            var nwMcX = mcCenter.x - me.map.getSize().width / 2 * zoomUnit;
            var nwMc = new BMap.Pixel(nwMcX, mcCenter.y + me.map.getSize().height / 2 * zoomUnit);

            var params = {
                points: me.points,
                size: size,
                nwMc: nwMc,
                zoomUnit: zoomUnit,
                mapSize: me.map.getSize(),
                mapCenter: me.map.getCenter(),
                zoom: zoom,
                griddingType: me.drawOptions.type
            };
            console.log("------")
            this.postMessage("GriddingOverlay.toRecGrids", params, function (gridsObj) {

                if (me.eventType == 'onmoving') {
                    return
                }
                ;

                var grids = gridsObj.grids;
                var max = gridsObj.max;
                var min = gridsObj.min;

                var obj = {
                    size: size,
                    zoomUnit: zoomUnit,
                    max: max,
                    min: min,
                    grids: grids
                };
                //清除
                me.ctx.clearRect(0, 0, me.ctx.canvas.width, me.ctx.canvas.height);
                me.canvasResize();
                me.drawRec(obj);

            });
        },
        drawRec: function (obj) {
            var size = obj.size;
            var zoomUnit = obj.zoomUnit;
            var max = obj.max;
            var min = obj.min;
            var grids = obj.grids;
            var gridStep = size / zoomUnit;
            var step = (max - min + 1) / 10;


            //是否有文字
            var lable = this.drawOptions.label && this.drawOptions.label.show;

            for (var i in grids) {
                var sp = i.split('_');
                var x = sp[0];
                var y = sp[1];
                var v = (grids[i] - min) / step;
                var color = this.drawOptions.bgColor ? this.drawOptions.bgColor(grids[i]) : this._getColorByGradient(grids[i], max, this.drawOptions.opacity);


                if (grids[i] === 0) {
                    this.ctx.fillStyle = 'rgba(255,255,255,0)';
                } else {
                    this.ctx.fillStyle = color;
                }
                this.ctx.fillRect(x, y, gridStep - this.drawOptions.padding, gridStep - this.drawOptions.padding);

                if (lable) {
                    this.ctx.save();
                    this.ctx.textBaseline = 'top';
                    if (grids[i] !== 0) {
                        this.ctx.fillStyle = 'rgba(0,0,0,0.8)';
                        this.ctx.fillText(grids[i], x, y);
                    }
                    this.ctx.restore();
                }
            }
        },
        setDrawOptions: function (opts) {
            for (var i in opts) {
                this.drawOptions[i] = opts[i];
            }
        },
        setDrawElement: function () {

        }
    });
    /*
     * 网格聚合网络
     */
    function GriddingOverlay2(points, opts) {
        CanvasOverlay.call(this, arguments);
        this.points = points;
        this.mouse = null;
        this.drawOptions = { // 绘制参数
            size: 50, // 网格大小
            opacity: '0.5',
            label: { // 是否显示文字标签
                show: true,
            },
            gradient: { // 显示的颜色渐变范围
                '0': 'blue',
                '0.6': 'cyan',
                '0.7': 'lime',
                '0.8': 'yellow',
                '1.0': 'red'
            },
            imgUrl: '',
            type: "sum", //sum 聚合权重累加  聚合权重平均
            padding: 0
        }

        this.setDrawOptions(opts);

        this.data = []; //缓存图片集合
        this.grids = []; //聚合结果

    }

    GriddingOverlay2.inherits(CanvasOverlay, "GriddingOverlay2");

    TD.extend(GriddingOverlay2.prototype, {
        resize: function () {
            this.setPoints();
        },
        _generalGradient: function (grad) {
            // create a 256x1 gradient that we'll use to turn a grayscale heatmap into a colored one
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');
            var gradient = ctx.createLinearGradient(0, 0, 0, 256);

            canvas.width = 1;
            canvas.height = 256;

            for (var i in grad) {
                gradient.addColorStop(i, grad[i]);
            }

            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, 1, 256);

            this._grad = ctx.getImageData(0, 0, 1, 256).data;
        },
        _getColorByGradient: function (count, max, opacity) {
            var maxF = max || 10;

            var index = count / maxF;
            if (index > 1) {
                index = 1;
            }
            index *= 255;
            index = parseInt(index, 10);
            index *= 4;

            var color = 'rgba(' + this._grad[index] + ', ' + this._grad[index + 1] + ', ' + this._grad[index + 2] + ', ' + (opacity || 0) + ')';
            return color;
        },
        setPoints: function (points) {
            var me = this;
            me.points = points || me.points;
            if (!me.ctx || !me.points) {
                return
            }


            var zoom = me.map.getZoom();
            var zoomUnit = Math.pow(2, 18 - zoom);
            var mercatorProjection = me.map.getMapType().getProjection();
            var mcCenter = mercatorProjection.lngLatToPoint(me.map.getCenter());
            var size = this.drawOptions.size * zoomUnit;
            var nwMcX = mcCenter.x - me.map.getSize().width / 2 * zoomUnit;
            var nwMc = new BMap.Pixel(nwMcX, mcCenter.y + me.map.getSize().height / 2 * zoomUnit);

            var params = {
                points: me.points,
                size: size,
                nwMc: nwMc,
                zoomUnit: zoomUnit,
                mapSize: me.map.getSize(),
                mapCenter: me.map.getCenter(),
                zoom: zoom,
                griddingType: me.drawOptions.type
            };
            console.log("------")
            this.postMessage("GriddingOverlay2.toRecGrids", params, function (gridsObj) {

                if (me.eventType == 'onmoving') {
                    return
                }
                ;

                var grids = gridsObj.grids;


                var obj = {
                    size: size,
                    zoomUnit: zoomUnit,

                    grids: grids
                };
                //清除
                me.ctx.clearRect(0, 0, me.ctx.canvas.width, me.ctx.canvas.height);
                me.canvasResize();
                me.drawRec(obj);

            });
        },
        drawRec: function (obj) {
            var me = this;

            var size = obj.size;
            var zoomUnit = obj.zoomUnit;

            var grids = obj.grids;
            this.grids = grids;

            //是否有文字
            var lable = this.drawOptions.label && this.drawOptions.label.show;
            var img = new Image();
            img.src = me.drawOptions.imgUrl;
            me.data = [];
            img.onload = function () {
                var left = img.width / 2;
                var top = img.height / 2;
                for (var i in grids) {
                    var sp = i.split('_');
                    var x = parseInt(( parseFloat(sp[0]) + me.drawOptions.size / 2) - left);
                    var y = parseInt((parseFloat(sp[1]) + me.drawOptions.size / 2) - top);
                    if (grids[i].length > 0) {
                        var obj = me.drawOptions.getSize(grids[i]);
                        var temp = new horerImage(i, x, y, obj.width, obj.height);
                        me.data.push(temp);
                        temp.draw(me.ctx, img);
                    }


                }
            }

        },
        bindEvent: function () {

            var me = this;
            this.map.addEventListener("mousemove", function (event) {

                for (var j = 0; j < me.data.length; j++) {
                    var per = me.data[j];
                    if (per.isMouseOver(event.pixel.x, event.pixel.y)) {

                        if (me.drawOptions.onMouseOver) {
                            me.drawOptions.onMouseOver(me.grids[per.id], event, true);
                        }

                        break;
                    } else {

                        if (me.drawOptions.onMouseLeave) {
                            me.drawOptions.onMouseLeave();
                        }
                    }
                }
            });
        },
        setDrawOptions: function (opts) {
            for (var i in opts) {
                this.drawOptions[i] = opts[i];
            }
        },
        setDrawElement: function () {
            this.mouse = captureMouse(this.container);
            this.bindEvent();
        }
    });
    function HeatGriddingOverlay(points, opts) {
        CanvasOverlay.call(this, arguments);
        this.points = points;
        var opts = opts || {};
        this.opts = {
            radius: opts.radius || 30,    // 半径
            gradient: opts.gradient || {
                0.25: "rgb(0,0,255)",
                0.55: "rgb(0,255,0)",
                0.85: "yellow",
                1.0: "rgb(255,0,0)"
            },    // gradient用于调色板
            minOpacity: opts.minOpacity || 0,    // 最小透明度
            maxOpacity: opts.maxOpacity || 0.8,    // 最大透明度
            minValue: opts.minValue || 0,    // 最小权重
            maxValue: opts.maxValue || 100,    // 最大权重
            minScope: opts.minScope || 0,    // 最小区间,小于此区间的不显示
            maxScope: opts.maxScope || 1	  // 最大区间,大于此区间的不显示
        };
        this.drawElement = null;
        this.map = null;
    }

//HeatGriddingOverlay.prototype = new CanvasOverlay();
    HeatGriddingOverlay.inherits(CanvasOverlay, "HeatGriddingOverlay");

    /**opts:
     * radius: 半径
     * gradient: gradient
     *
     *
     */
    TD.extend(HeatGriddingOverlay.prototype, {
        resize: function () {
            console.log('resize')
            this.setPoints();
        },

        setPoints: function (points) {
            var me = this;
            points = points || this.points;
            if (!this.drawElement || !points) {
                return
            }
            this.points = points;
            var pixels = [];
            var ctx = this.getContext(), p, pixel;


            //by maji
            this.postMessage('HeatOverlay.pointsToPixels', points, function (pixels) {
                var size = map.getSize();
                me.getContext().clearRect(0, 0, size.width, size.height);//调整画布
                me.canvasResize(me);

                for (var i = 0, len = pixels.length; i < len; i++) {
                    var opacity = (pixels[i].count - me.opts.minValue) / (me.opts.maxValue - me.opts.minValue);
                    me.drawElement.drawPoint(pixels[i].x + me.margin, pixels[i].y + me.margin, me.opts.radius, opacity);
                }
                me.drawElement.drawColor();
            });
            /****

             for(var i=0,len = points.length; i<len; i++) {
//			pixel = map.pointToOverlayPixel(points[i]);

			var point = new BMap.Point(points[i]['lng'], points[i]['lat']);
			pixel = TD.pointToPixel(point, map);
			pixels.push({
				x: pixel.x + this.margin,
				y: pixel.y + this.margin,
				count: points[i].count
			});

			var count = points[i]['count'];
			var opacity = (count - this.opts.minValue)  / (this.opts.maxValue - this.opts.minValue);
			this.drawElement.drawPoint(pixel.x + this.margin, pixel.y + this.margin, this.opts.radius, opacity);
		}
             //console.log(JSON.stringify(pixels));
             this.drawElement.drawColor();
             ***/
        },

        setOptions: function (opts) {
            for (var i in opts) {
                this.opts[i] = opts[i];
            }
            this.setPoints();
        },

        setDrawElement: function () {
            this.drawElement = new Gridding(this.container, this.ctx, this.opts);
        }


    });
    function HeatOverlay(points, opts) {
        CanvasOverlay.call(this, arguments);
        this.points = points;
        var opts = opts || {};
        this.default_gradient_circle = {
            0.25: "rgb(0,0,255)",
            0.55: "rgb(0,255,0)",
            0.85: "yellow",
            1.0: "rgb(255,0,0)"
        };
        this.default_gradient_rec = {
            0.1: "rgb(37, 115, 1)",
            0.2: "rgb(58, 167, 0)",
            0.3: "rgb(78, 229, 0)",
            0.4: "rgb(152, 229, 1)",
            0.5: "rgb(208, 251, 115)",
            0.6: "rgb(247, 224, 1)",
            0.7: "rgb(255, 85, 0)",
            0.8: "rgb(230, 33, 0)",
            1.0: "rgb(180, 21, 0)"
        };
        this.opts = {
            radius: opts.radius || 30,    // 半径
            minOpacity: opts.minOpacity || 0,    // 最小透明度
            maxOpacity: opts.maxOpacity || 0.8,    // 最大透明度
            minValue: opts.minValue || 0,    // 最小权重
            maxValue: opts.maxValue || 100,    // 最大权重
            minScope: opts.minScope || 0,    // 最小区间,小于此区间的不显示
            maxScope: opts.maxScope || 1,	  // 最大区间,大于此区间的不显示
            type: opts.type || 'circle'    // 图形,默认普通circle;rec是马赛克
        };
        // 判断形状,设置颜色区间,用于调色板
        if (opts.gradient) {
            this.opts.gradient = opts.gradient;
        } else {
            if (this.opts.type === 'rec') {
                this.opts.gradient = this.default_gradient_rec;
            } else if (this.opts.type === 'circle') {
                this.opts.gradient = this.default_gradient_circle;
            }
        }
        this.drawElement = null;
        this.map = null;
    }

//HeatOverlay.prototype = new CanvasOverlay();
    HeatOverlay.inherits(CanvasOverlay, "HeatOverlay");

    /**opts:
     * radius: 半径
     * gradient: gradient
     *
     *
     */
    TD.extend(HeatOverlay.prototype, {
        resize: function () {
            console.log('resize')
            this.setPoints();
        },

        setPoints: function (points, callback) {
            var me = this;
            points = points || this.points;
            if (!this.drawElement || !points) {
                return
            }
            this.points = points;
            var pixels = [];
            var ctx = this.getContext(), p, pixel;
            var t1 = new Date()
            //by maji
            this.postMessage('HeatOverlay.pointsToPixels', points, function (pixels) {
                var t2 = new Date()
                // var size = map.getSize();
                if (me.eventType == 'onmoving') {
                    return
                }
                ;
                me.clearCanvas();


                for (var i = 0, len = pixels.length; i < len; i++) {
                    var opacity = (pixels[i].count - me.opts.minValue) / (me.opts.maxValue - me.opts.minValue);
                    me.drawElement.drawPoint(pixels[i].x + me.margin, pixels[i].y + me.margin, me.opts.radius, opacity);
                }
                var t3 = new Date()
                me.canvasResize(me);
                me.drawElement.drawColor();
                var t4 = new Date();
                console.log(t2 - t1, t3 - t2, t4 - t3)

                if(callback!=null){
                    callback();
                }
            });


            /*
             me.clearCanvas();
             var t1 = new Date()
             for(var i=0,len = points.length; i<len; i++) {
             //			pixel = map.pointToOverlayPixel(points[i]);

             var point = new BMap.Point(points[i]['lng'], points[i]['lat']);
             pixel = TD.pointToPixel(point, map);
             pixels.push({
             x: pixel.x + this.margin,
             y: pixel.y + this.margin,
             count: points[i].count
             });

             var count = points[i]['count'];
             var opacity = (count - this.opts.minValue)  / (this.opts.maxValue - this.opts.minValue);
             this.drawElement.drawPoint(pixel.x + this.margin, pixel.y + this.margin, this.opts.radius, opacity);
             }
             //console.log(JSON.stringify(pixels));
             me.canvasResize(me);
             var t2 = new Date()
             this.drawElement.drawColor();
             var t3 = new Date()
             console.log('time', t1.getTime(), t2.getTime(), t3.getTime(), t3 - t2, t2- t1)
             */
        },

        setOptions: function (opts) {
            for (var i in opts) {
                this.opts[i] = opts[i];
            }
            // 判断形状,设置颜色区间,用于调色板
            if (opts.gradient) {
                this.opts.gradient = opts.gradient;
            } else {
                if (this.opts.type === 'rec') {
                    this.opts.gradient = this.default_gradient_rec;
                } else if (this.opts.type === 'circle') {
                    this.opts.gradient = this.default_gradient_circle;
                }
            }
            this.setPoints();
        },

        setDrawElement: function () {
            this.drawElement = new GradientCircle(this.container, this.ctx, this.opts);
        }


    });
    /*
     * 蜂窝聚合
     */
    function HoneycombOverlay(points, opts) {
        CanvasOverlay.call(this, arguments);
        this.points = points;
        this.drawOptions = { // 绘制参数
            size: 50, // 网格大小
            opacity: '0.5',
            label: { // 是否显示文字标签
                show: true,
            },
            gradient: { // 显示的颜色渐变范围
                '0': 'blue',
                '0.6': 'cyan',
                '0.7': 'lime',
                '0.8': 'yellow',
                '1.0': 'red'
            }
        }
        this._grad = null;
        this._generalGradient(this.drawOptions.gradient);
        this.setDrawOptions(opts);
    }

    HoneycombOverlay.inherits(CanvasOverlay, "HoneycombOverlay");


    TD.extend(HoneycombOverlay.prototype, {
        resize: function () {
            this.setPoints();
        },
        _generalGradient: function (grad) {
            // create a 256x1 gradient that we'll use to turn a grayscale heatmap into a colored one
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');
            var gradient = ctx.createLinearGradient(0, 0, 0, 256);

            canvas.width = 1;
            canvas.height = 256;

            for (var i in grad) {
                gradient.addColorStop(i, grad[i]);
            }

            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, 1, 256);

            this._grad = ctx.getImageData(0, 0, 1, 256).data;
        },
        _getColorByGradient: function getColorByGradient(count, max, opacity) {
            var maxF = max || 10;

            var index = count / maxF;
            if (index > 1) {
                index = 1;
            }
            index *= 255;
            index = parseInt(index, 10);
            index *= 4;

            var color = 'rgba(' + this._grad[index] + ', ' + this._grad[index + 1] + ', ' + this._grad[index + 2] + ', ' + (opacity || 0) + ')';
            return color;
        },
        setPoints: function (points) {
            this.points = points || this.points;
            if (!this.ctx || !this.points) {
                return
            }
            var me = this;

            var zoom = me.map.getZoom();
            var zoomUnit = Math.pow(2, 18 - zoom);
            var mercatorProjection = me.map.getMapType().getProjection();
            var mcCenter = mercatorProjection.lngLatToPoint(me.map.getCenter());
            var size = parseInt(this.drawOptions.size, 10) * zoomUnit;
            var nwMcX = mcCenter.x - me.map.getSize().width / 2 * zoomUnit;
            var nwMc = new BMap.Pixel(nwMcX, mcCenter.y + me.map.getSize().height / 2 * zoomUnit);

            var params = {
                points: me.points,
                size: size,
                nwMc: nwMc,
                zoomUnit: zoomUnit,
                mapSize: me.map.getSize(),
                mapCenter: me.map.getCenter(),
                zoom: zoom
            };

            this.postMessage("HoneycombOverlay.toRecGrids", params, function (gridsObj) {
                if (me.eventType == 'onmoving') {
                    return
                }
                ;
                me.ctx.clearRect(0, 0, me.ctx.canvas.width, me.ctx.canvas.height);
                me.canvasResize();

                var grids = gridsObj.grids;
                var max = gridsObj.max;
                var min = gridsObj.min;

                var obj = {
                    size: size,
                    zoomUnit: zoomUnit,
                    max: max,
                    min: min,
                    grids: grids,
                    margin: me.margin
                };
                me.drawHoneycomb(obj);
            });
        },
        drawHoneycomb: function (obj) {

            var grids = obj.grids;
            var gridsW = obj.size / obj.zoomUnit;

            var color = obj.color;
            //是否有文字
            var lable = this.drawOptions.label && this.drawOptions.label.show;

            for (var i in grids) {
                var x = grids[i].x;
                var y = grids[i].y;
                var count = grids[i].len;
                if (count > 0) {
                    var color = obj.color ? obj.color : this._getColorByGradient(count, obj.max, this.drawOptions.opacity);
                    this.drawLine(x, y, gridsW - 1, color, this.ctx);
                }

                if (lable && count !== 0) {
                    this.ctx.save();
                    this.ctx.textBaseline = 'middle';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillStyle = 'rgba(0,0,0,0.8)';
                    this.ctx.fillText(count, x, y);
                    this.ctx.restore();

                }
            }

        },
        setDrawOptions: function (opts) {
            for (var i in opts) {
                this.drawOptions[i] = opts[i];
            }
        },
        setDrawElement: function () {

        },
        drawLine: function (x, y, gridStep, color, ctx) {
            ctx.beginPath();
            ctx.fillStyle = color;

            ctx.moveTo(x, y - gridStep / 2);
            ctx.lineTo(x + gridStep / 2, y - gridStep / 4);
            ctx.lineTo(x + gridStep / 2, y + gridStep / 4);
            ctx.lineTo(x, y + gridStep / 2);
            ctx.lineTo(x - gridStep / 2, y + gridStep / 4);
            ctx.lineTo(x - gridStep / 2, y - gridStep / 4);
            ctx.fill();
            ctx.closePath();
        }
    });
    /**
     * Created by tendcloud on 2016/1/28.
     */
    /*
     * 点的绘制
     */
    function ImageOverlay(points, opts) {
        CanvasOverlay.call(this, arguments);
        this.points = points;
        this.drawOptions = {
            fillStyle: null, // 填充颜色
            lineWidth: 0,                       // 描边宽度
            shadowColor: null, // 投影颜色
            shadowBlur: 0,                      // 投影模糊级数
            globalCompositeOperation: null, // 颜色叠加方式
            size: 4, // 半径
            imgUrl: null

        };
        this.drawElement = null;
        this.map = null;
        this.setDrawOptions(opts);
        this.data = [];

    }

    ImageOverlay.inherits(CanvasOverlay, "ImageOverlay");

    TD.extend(ImageOverlay.prototype, {
        resize: function () {
            this.setPoints();
        },

        setPoints: function (points) {
            var me = this;
            this.points = points || this.points;

            var pixels = [];
            var img = new Image();
            img.src = me.drawOptions.imgUrl;

            img.onload = function () {
                me.postMessage('HeatOverlay.pointsToPixels', me.points, function (pixels) {
                    if (me.eventType == 'onmoving') {
                        return;
                    }
                    var size = me.map.getSize();
                    me.getContext().clearRect(0, 0, size.width, size.height);//调整画布
                    me.canvasResize(me);
                    me._setCtx();


                    me.data = [];
                    var drawOptions = me.drawOptions;
                    for (var i = 0; i < pixels.length; i++) {
                        var pixel = pixels[i];

                        var obj = me.drawOptions.getSize(pixel);
                        var temp = new horerImage(null, pixel.x, pixel.y, obj.width, obj.height);
                        me.data.push(temp);
                        temp.draw(me.ctx, img);

                    }


                });
            }
        },
        bingEvent: function () {
            var me = this;
            me.map.addEventListener("mousemove", function (event) {

                for (var j = 0; j < me.data.length; j++) {
                    var per = me.data[j];
                    if (per.isMouseOver(event.pixel.x, event.pixel.y)) {

                        if (me.drawOptions.onMouseOver) {
                            me.drawOptions.onMouseOver(me.points[j], event, true);
                        }

                        break;
                    } else {

                        if (me.drawOptions.onMouseLeave) {
                            me.drawOptions.onMouseLeave();
                        }
                    }
                }
            });


        },
        setDrawOptions: function (opts) {
            for (var i in opts) {
                this.drawOptions[i] = opts[i];
            }
        },
        _setCtx: function () {
            if (this.drawOptions.shadowBlur) {
                this.ctx.shadowBlur = this.drawOptions.shadowBlur;
            }
            if (this.drawOptions.shadowColor) {
                this.ctx.shadowColor = this.drawOptions.shadowColor;
            }
            if (this.drawOptions.globalCompositeOperation) {
                this.ctx.globalCompositeOperation = this.drawOptions.globalCompositeOperation;
            }
            if (this.drawOptions.lineWidth) {
                this.ctx.lineWidth = this.drawOptions.lineWidth;
            }
        },
        setDrawElement: function () {

            this.bingEvent();
        },
        setDraw: function (cir) {

        }
    });
    /**
     * 室内地图覆盖物类
     * @param {String} imgurl  地图URL
     * @param {Int} width
     * @param {Int} height
     * @param {String} align       auto || width || height
     */
    function IndoorOverlay(imgurl, width, height, align) {
        TD.BaseClass.call(this);
        this.imgurl = imgurl;	//室内地图图片URL
        this.width = width;
        this.height = height;
        this.imgZoom = 1;			//当前缩放级别
        this.image = new Image();	//创建地图图片实例
        this.margin = 0;
        this.defaultLevel = 20;		//初始化地图级别
        this.defaultCenter = null;	//初始化地图中心点
        this.defaultInfo = {}		//初始化室内地图图片信息,{width:,height:,left:,top:}
        this.nowInfo = {}			//当前信息
        this.align = align || 'auto';
    }

    IndoorOverlay.inherits(BMap.Overlay, "IndoorOverlay");
    TD.extend(IndoorOverlay.prototype, {
        initialize: function (map) {
            var me = this;
            this.map = map;
            var zoom = map.getZoom();
            this.defaultLevel = zoom;
            map.setMaxZoom(zoom + 2);
            map.setMinZoom(zoom - 2);
            map.addEventListener('tilesloaded', function (e) {
                me.hideTileLayer()
            })

            this.container = document.createElement('div');
            var size = map.getSize();
            this.container.style.cssText = 'position:absolute;left:' + size.width / 2 + 'px;top:' + size.height / 2 + 'px;width:5px;height:5px';
            this.image.onload = function () {
                me.imageLoad();
            };
            this.image.src = this.imgurl;

            map.getPanes().labelPane.appendChild(this.container);
            var parentDiv = map.getPanes().labelPane.parentNode.parentNode;
            this.hideTileLayer();

            var size = map.getSize();

            map.addEventListener('zoomend', function (e) {
                me.zoomTo(this.getZoom());
                setTimeout(function () {
                    parentDiv.style.marginTop = 0;
                }, 50)
            })

            map.addEventListener('zoomstart', function (e) {
                parentDiv.style.marginTop = '-10000px';
                var a = 1;
            })
            //this.getViewport();
            //		map.addEventListener('resize', function(event){
            //			me.setCanvasSize();
            //			me._draw(me, event);
            //		});
            //
            //		map.addEventListener("load", function(e){me._draw(me, e)});
            //		map.addEventListener("moveend", function(e){me._draw(me, e);me.eventType = e.type});
            //		map.addEventListener("zoomstart", function(e){me.clearCanvas()});
            //		map.addEventListener("zoomend", function(e){me._draw(me, e)});
            //		map.addEventListener("moving", function(e){me.eventType = e.type})
            //
            //		this.setDrawElement();
            //		this._overlayParentZIndex();
            return this.container;
        }
        , draw: function (e) {
        }

        , resize: function () {

        }
        /**
         * 室内地图load完成
         */
        , imageLoad: function () {

            var defaultInfo = this.defaultInfo = this.getMapAlign();
            this.defaultCenter = this.map.getCenter();
            //初始化地图bound
            var size = this.map.getSize();
            this.defaultLevel = this.map.getZoom();
            this.imgZoom = defaultInfo.zoom	// Math.pow(2, defaultInfo.zoom);
            //左下角经纬度坐标
            var pointLB = this.map.pixelToPoint(new BMap.Pixel(size.width / 2 - defaultInfo.width / 2, size.height / 2 + defaultInfo.height / 2));
            //右上角经纬度坐标
            var pointRT = this.map.pixelToPoint(new BMap.Pixel(size.width / 2 + defaultInfo.width / 2, size.height / 2 - defaultInfo.height / 2));
            this.bounds = new BMap.Bounds(pointLB, pointRT);

            this.nowInfo = defaultInfo;
            this.image.style.cssText = 'position:absolute;width:' + defaultInfo.width + 'px; height: ' + defaultInfo.height + 'px;left:' + defaultInfo.left + 'px;top:' + defaultInfo.top + 'px';
            this.container.appendChild(this.image);
            this.container.parentNode.style.zIndex = 150;
            //派发load事件
            this.dispatchEvent(new TD.BaseEvent('onload'));
        }
        /**
         * 设置地图对齐
         */
        , getMapAlign: function () {
            var map = this.map;
            var size = map.getSize();
            var mapw = size.width;
            var maph = size.height;
            var mapScale = mapw / maph;

            var imgw = this.width;
            var imgh = this.height;
            var imgScale = imgw / imgh;

            var obj = {}

            /**
             * 宽优先
             */
            function widthFirst() {
                obj.width = mapw;
                obj.height = mapw / imgScale;
                obj.left = 0 - size.width / 2;
                obj.top = (maph - obj.height) / 2 - size.height / 2;
                obj.zoom = obj.height / imgh;

                return obj;
            }

            /**
             * 高优先
             */
            function heightFirst() {

                obj.width = maph * imgScale;
                obj.height = maph;
                obj.left = (mapw - obj.width) / 2 - size.width / 2;
                obj.top = 0 - size.height / 2;
                obj.zoom = obj.width / imgw;
                return obj;
            }

            /**
             * 真实大小
             */
            function realImg() {
                obj.width = imgw;
                obj.height = imgh;
                obj.top = -imgh / 2;
                obj.left = -imgw / 2;
                obj.zoom = 1;
                return obj;
            }

            switch (this.align) {
                //宽优先
                case 'width':
                    return widthFirst();
                //高优先
                case 'height':
                    return heightFirst();
                //全部显示
                default:
                    if (mapw > imgw && maph > imgh) {
                        return realImg();
                    }
                    if (mapScale > imgScale) {
                        return heightFirst();
                    } else {
                        return widthFirst();
                    }
            }
        }

        , zoomTo: function (zoom) {
            if (!zoom || !this.defaultInfo) return;
            var defaultInfo = this.defaultInfo;
            var defaultImgZoom = this.defaultLevel;
            var mapOffest = this.map.pointToOverlayPixel(this.defaultCenter || this.map.getCenter());
            this.container.style.left = mapOffest.x + 'px';
            this.container.style.top = mapOffest.y + 'px';

            this.imgZoom = Math.pow(2, zoom - defaultImgZoom);


            var width = defaultInfo.width * this.imgZoom;
            var height = defaultInfo.height * this.imgZoom;
            var left = -width / 2;
            var top = -height / 2;
            this.image.style.width = width + 'px';
            this.image.style.height = height + 'px';
            this.image.style.left = left + 'px';
            this.image.style.top = top + 'px';
            this.nowInfo = {
                width: width
                , height: height
                , left: left
                , top: top
            };

        }


        , getViewport: function () {
            if (!this.map) return;
            var map = this.map;
            var width = this.width;
            var height = this.height;

            var viewPort = map.getViewport([map.pixelToPoint(new BMap.Pixel(0, height)), map.pixelToPoint(new BMap.Pixel(width, 0))]);
            var center = viewPort.center;
            var level = viewPort.level;

        }


        /**
         * 隐藏百度地图瓦片
         */
        , hideTileLayer: function () {

            var map = this.map;
            var mapContainer = map.getContainer();
            var tiles = mapContainer.getElementsByTagName('IMG');
            var cvs = mapContainer.getElementsByTagName('canvas');
            var tplDiv = document.createElement('div');
            if (tiles.length == 0 && cvs.length == 0) return;
            //PC 图片瓦片
            for (var i = 0, len = tiles.length; i < len; i++) {
                if (tiles[i].src.indexOf('bdimg.com/tile/') > 0) {
                    tiles[i].parentNode.parentNode.setAttribute('tile', 'tileDiv')
                    tiles[i].parentNode.parentNode.style.display = 'none'
                    tiles[i].parentNode.parentNode.innerHTML = '';
                    return;
                }
            }
            //无线canva瓦片
            for (var j = 0, len = cvs.length; j < len; j++) {
                if (!!cvs[j] && !!cvs[j].id && cvs[j].id.indexOf('_') == 0) {
                    cvs[j].parentNode.parentNode.style.display = 'none';
                    tplDiv.appendChild(cvs[j].parentNode.parentNode);
                    return;
                }
            }

        }
        /**
         * 获取室内地图地理bounds
         */
        , getBounds: function () {
            return this.bounds;
        }
        , getZoom: function () {
            return this.defaultInfo.zoom;
        }
        /**
         *
         */
        , getMapSize: function () {
            if (!this.bounds) return;
            return {}
        }
        /**
         *
         */
        , setBackground: function (color) {
            var container = this.map.getContainer();
            container.style.background = color;
        }
        /**
         * 获取当前级别下，坐标原点像素坐标
         */
        , getOrigin: function () {
            var bounds = this.getBounds();
            if (!bounds) return;
            //西南角像素
            var sw = this.map.pointToPixel(bounds.getSouthWest());
            var ne = this.map.pointToPixel(bounds.getNorthEast());
            var origin = new BMap.Pixel(sw.x, ne.y);
            return origin;
        }

        /**
         * 室内地图像素坐标转经纬度
         */
        , inPixelToPoint: function (x, y) {
            var origin = this.getOrigin();
            if (!origin) return;
            var imgScale = this.width / (this.nowInfo.width || this.defaultInfo.width);
            console.log('imgScale', imgScale)
            //		var point = this.map.pixelToPoint(new BMap.Pixel((origin.x + x *this.imgZoom), (origin.y + y*this.imgZoom)));
            var point = this.map.pixelToPoint(new BMap.Pixel((origin.x + x / imgScale), (origin.y + y / imgScale)));
            return point;

        }
        , pointToInPixel: function (point) {
            var origin = this.getOrigin();
            if (!origin) return;
            var pixel = this.map.pointToPixel(point);
            var imgScale = this.width / (this.nowInfo.width || this.defaultInfo.width);
            //var inPixel = {x: (pixel.x - origin.x) / this.imgZoom, y : (pixel.y - origin.y) / this.imgZoom};
            //console.log(this.width, this.defaultInfo.width, this.imgZoom, (this.defaultInfo.width))
            //console.log(pixel.x, origin.x, imgScale)
            var inPixel = {x: (pixel.x - origin.x) * imgScale, y: (pixel.y - origin.y) * imgScale};
            return inPixel;
        }

    });
    /*
     * 点的绘制
     */
    function Marker(opts) {
        CanvasOverlay.call(this, arguments);
        this.mouse = null;
        this.drag = null; //拖拽元素
        this.drawOptions = {
            anBorderColor: null, //同比边框
            anBgColor: null, //同比背景
            thanBorderColor: null, //环比边框
            thanBgColor: null, //环比背景
            ellipseSize: 0,  //椭圆扁扁平系数
            onMouseOver: null,
            onMOuseLeave: null,
            draw: TDMap.Probe,
            imgsrc1: opts.imgsrc1,
            imgsrc2: opts.imgsrc2,
            isDrag: false //是否拖拽
        };
        this.setDrawOptions(opts);
        this.points = [];
        this.img1 = null;
        this.img2 = null;
        this.isLoadImg = false;
    }

    Marker.inherits(CanvasOverlay, "Marker");

    TD.extend(Marker.prototype, {
        resize: function () {
            this.draw();
        },
        clear: function () {
            var size = this.map.getSize();
            this.getContext().clearRect(0, 0, size.width, size.height);//调整画布
        },
        loadImg: function (fun) {
            var me = this;
            if (this.isLoadImg) {
                fun(me.img1, me.img2);
            } else {
                var img1 = new Image();
                img1.src = me.drawOptions.imgsrc1;
                img1.onload = function () {
                    me.isLoadImg = true;
                    var img2 = new Image();
                    img2.src = me.drawOptions.imgsrc2;

                    img2.onload = function () {
                        me.img1 = img1;
                        me.img2 = img2;
                        fun(me.img1, me.img2);
                    }
                }
            }
        },
        setPoints: function (data) {
            if (!this.ctx) {
                return;
            }
            var me = this;

            me.loadImg(function (img1, img2) {

                for (var i = 0; i < data.length; i++) {
                    me.points.push(
                        new me.drawOptions.draw({
                            anBorderColor: me.drawOptions.anBorderColor,
                            anBgColor: me.drawOptions.anBgColor,
                            anRadius: data[i].anRadius,
                            thanBorderColor: me.drawOptions.thanBorderColor,
                            thanBgColor: me.drawOptions.thanBgColor,
                            thanRadius: data[i].thanRadius,
                            ellipseSize: me.drawOptions.ellipseSize,
                            pixelX: data[i].pixelX,
                            pixelY: data[i].pixelY,
                            img1: img1,
                            img2: img2,
                            id: data[i].id
                        }));
                }
                me.draw();
            });


        },
        draw: function () {
            if (this.points) {
                this.clear();
                for (var i = 0; i < this.points.length; i++) {
                    this.points[i].draw(this.ctx);
                }
            }

        },
        onMousemove: function (me, event) {
            for (var j = 0; j < this.points.length; j++) {
                var per = me.points[j];
                if (per.containstop(me.mouse.x, me.mouse.y)) {
                    if (me.drawOptions.isDrag) {
                        this.map.setDefaultCursor("move");
                    } else {
                        if (me.drawOptions.onMouseOver) {
                            me.drawOptions.onMouseOver(per, event, true);
                        }
                    }
                    break;
                } else if (per.containsRing(me.mouse.x, me.mouse.y)) {
                    this.map.setDefaultCursor("default");
                    if (me.drawOptions.onMouseOver) {
                        me.drawOptions.onMouseOver(per, event, false);
                    }
                    break;
                } else {
                    this.map.setDefaultCursor("default");
                    if (me.drawOptions.onMouseLeave) {
                        me.drawOptions.onMouseLeave();
                    }
                }
            }
        },

        bindEvent: function () {
            var me = this;
            me.container.addEventListener("mousemove", function () {

                if (me.drag && me.drawOptions.isDrag) {
                    me.drag.pixelX = me.mouse.x;
                    me.drag.pixelY = me.mouse.y + me.drag.img2.height;
                    me.draw();
                } else {
                    me.onMousemove(me, event);
                }
            }, false);
            me.container.addEventListener('mousedown', function () {
                if (me.drawOptions.isDrag) {
                    for (var i = 0; i < me.points.length; i++) {
                        var pelbeMar = me.points[i];
                        if (pelbeMar.containstop(me.mouse.x, me.mouse.y)) {
                            me.drag = pelbeMar;
                            map.setDefaultCursor("move");
                            break;
                        }
                    }
                }

            }, false);
            me.container.addEventListener('mouseup', function () {
                if (me.drawOptions.isDrag) {
                    me.drag = null;
                    map.setDefaultCursor("default");
                }

            }, false);
        },
        setDrawElement: function () {
            this.mouse = captureMouse(this.container);
            this.bindEvent();
            this.map.setDefaultCursor("default");
        },
        setDrawOptions: function (opts) {
            for (var i in opts) {
                this.drawOptions[i] = opts[i];
            }
        },
    });
    /**
     * Created by tendcloud on 2016/2/15.
     */
    /*
     * 网格聚合网络
     */
    function PointAggregationsOverlay(points, opts) {
        CanvasOverlay.call(this, arguments);
        this.points = points;
        this.drawOptions = { // 绘制参数
            size: 50, // 网格大小
            opacity: '0.5',
            label: { // 是否显示文字标签
                show: true
            },

        };

        this.setDrawOptions(opts);


    }

    PointAggregationsOverlay.inherits(CanvasOverlay, "PointAggregationsOverlay");

    TD.extend(PointAggregationsOverlay.prototype, {
        resize: function () {
            this.setPoints();
        },


        setPoints: function (points) {
            var me = this;
            me.points = points || me.points;
            if (!me.ctx || !me.points) {
                return
            }


            var zoom = me.map.getZoom();
            var zoomUnit = Math.pow(2, 18 - zoom);
            var mercatorProjection = me.map.getMapType().getProjection();
            var mcCenter = mercatorProjection.lngLatToPoint(me.map.getCenter());
            var size = this.drawOptions.size * zoomUnit;
            var nwMcX = mcCenter.x - me.map.getSize().width / 2 * zoomUnit;
            var nwMc = new BMap.Pixel(nwMcX, mcCenter.y + me.map.getSize().height / 2 * zoomUnit);

            var params = {
                points: me.points,
                size: size,
                nwMc: nwMc,
                zoomUnit: zoomUnit,
                mapSize: me.map.getSize(),
                mapCenter: me.map.getCenter(),
                zoom: zoom
            };

            this.postMessage("PointAggregations.toRecGrids", params, function (gridsObj) {

                if (me.eventType == 'onmoving') {
                    return
                }


                var grids = gridsObj.grids;
                var max = gridsObj.max;
                var min = gridsObj.min;

                var obj = {
                    size: size,
                    zoomUnit: zoomUnit,
                    max: max,
                    min: min,
                    grids: grids
                };
                //清除
                me.ctx.clearRect(0, 0, me.ctx.canvas.width, me.ctx.canvas.height);
                me.canvasResize();
                me.drawRec(obj);

            });
        },
        drawRec: function (obj) {
            var size = obj.size;
            var zoomUnit = obj.zoomUnit;
            var max = obj.max;
            var min = obj.min;
            var grids = obj.grids;
            var gridStep = size / zoomUnit;
            var step = (max - min + 1) / 10;

            //是否有文字
            var lable = this.drawOptions.label && this.drawOptions.label.show;

            for (var i in grids) {
                var sp = i.split('_');
                var x = sp[0];
                var y = sp[1];
                var v = (grids[i] - min) / step;
                v = v < 0 ? 0 : v;
                var cx = x + gridStep / 2;
                var cy = y + gridStep / 2;

                this.ctx.fillStyle = this.drawOptions.bgColor === 'string' ? this.drawOptions.bgColor : this.drawOptions.bgColor(grids[i]);

                this.ctx.beginPath();

                this.ctx.arc(cx, cy, v * 5, 0, 2 * Math.PI);
                this.ctx.fill();
                this.ctx.lineWidth = 8 * v / 10;
                this.ctx.strokeStyle = this.drawOptions.strokeStyle || '#fff';
                this.ctx.stroke();
                if (lable) {
                    this.ctx.save();
                    this.ctx.font = 30 * v / 10 + 'px serif';
                    this.ctx.textAlign = 'center';
                    this.ctx.textBaseline = 'middle';
                    if (grids[i] !== 0) {
                        this.ctx.fillStyle = 'rgba(0,0,0,0.8)';
                        this.ctx.fillText(grids[i], x, y);

                    }
                    this.ctx.restore();
                }
            }
        },
        setDrawOptions: function (opts) {
            for (var i in opts) {
                this.drawOptions[i] = opts[i];
            }
        },
        setDrawElement: function () {

        }
    });
    window.TDMap = {
        CanvasOverlay: CanvasOverlay
        , HeatOverlay: HeatOverlay
        , DemoOverlay: DemoOverlay
        , DotOverlay: DotOverlay
        , MapStyle: MapStyle
        , BoundaryOverlay: BoundaryOverlay
        , GriddingOverlay: GriddingOverlay
        , GriddingOverlay2: GriddingOverlay2
        , HoneycombOverlay: HoneycombOverlay
        , HeatGriddingOverlay: HeatGriddingOverlay
        , IndoorOverlay: IndoorOverlay
        , Lamp: Lamp
        , Circle: Circle
        , DoodleOverlay: DoodleOverlay
        , Probe: Probe
        , Marker: Marker
        , DotDragOverlay: DotDragOverlay
        , horerCircle: horerCircle
        , PointAggregationsOverlay: PointAggregationsOverlay
        , ImageOverlay: ImageOverlay
    };
})
()