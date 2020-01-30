/**
 * 是否是函数
 * @param {Mix}
 * @returns {Boolean}
 */
function isFunction(func){
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
 * 是否是字符串ht
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
//postMessage('xxxx');
var window = window || self;
var TD = TD || {};
var TDMap = TDMap || {};
/**
 * 将source中的所有属性拷贝到target中。
 * @param {Object} target 属性的接收者
 * @param {Object} source 属性的来源
 * @return {Object} 返回的内容是o
 */
TD.extend = function(target, source){

    if(target && source && typeof(source) == "object"){
        for(var p in source){
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


/**
 * 接收worker消息
 * @param {Event} e
 */
TD.message = function(e){
    var data = e.data;
    TD.callback(data);
}
/**
 * 唯一生效队列控制全家对象
 */
TD.handler = {}
/**
 * worker方法执行解析
 */
TD.callback = function(data){
//	console.log('TD.callback', data)
    var request = data.request;
    var classPath = request.classPath;
    var hashCode = request.hashCode;
    var msgId = request.msgId;
    var p = classPath.split('.'),
        index = 0, callback = window;
    while (p[index]){
        callback = callback[p[index]];
        index++;
        if(index >= p.length){
            //唯一生效队列控制
            TD.handler[classPath] = hashCode +'_'+ msgId;
            //查找到执行方法，并执行方法
            var json = callback(data);
            return;
        }

        if(!callback){
            console.log(p[index-1] +'worker '+ classPath +' is not a function');
            return;
        }
    }
}

window.addEventListener('message', TD.message);
/**
 * push到web消息
 * @param {Object} data
 */
TD.postMessage = function(json, data){
    var opts = data;


    var request = data.request;
    var classPath = request.classPath;
    var hashCode = request.hashCode;
    var msgId = request.msgId;
    var handler = TD.handler[classPath];
    //唯一生效队列判断
    if(handler && (handler != hashCode +'_'+ msgId)){return};

    opts.response = {
        type :'worker'
        ,data : json
    }
    postMessage(opts)
}


var window = window || self;
var TD = TD || {};
var TDMap = TDMap || {};
//本算法的思想是把地图分成多个网格，当要计算的点落入某个网格时，将选取该网格最近的点进行匹配转换。
//使用尽量多的参考点，形成格网,选取的点越多，格网越密集，格网四边形越趋近于正方形，则精度越高
//目前点集形成格网精度10m
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
            {j: 116.381837, w: 40.000198, utm_x: 12955707.8 , utm_y: 4838247.62, x: 667412, y: 561832},
            {j: 116.430651, w: 39.995216, utm_x: 12961141.81, utm_y: 4837526.55, x: 686556, y: 573372},
            {j: 116.474111, w: 39.976323, utm_x: 12965979.81, utm_y: 4834792.55, x: 697152, y: 586816},
            {j: 116.280328, w: 39.953159, utm_x: 12944407.75, utm_y: 4831441.53, x: 603272, y: 549976},
            {j: 116.316117, w: 39.952496, utm_x: 12948391.8 , utm_y: 4831345.64, x: 618504, y: 557872},
            {j: 116.350477, w: 39.938107, utm_x: 12952216.78, utm_y: 4829264.65, x: 627044, y: 568220},
            {j: 116.432025, w: 39.947158, utm_x: 12961294.76, utm_y: 4830573.59, x: 666280, y: 584016},
            {j: 116.46873 , w: 39.949516, utm_x: 12965380.79, utm_y: 4830914.63, x: 683328, y: 591444},
            {j: 116.280077, w: 39.913823, utm_x: 12944379.8 , utm_y: 4825753.62, x: 586150, y: 558552},
            {j: 116.308625, w: 39.91374 , utm_x: 12947557.79, utm_y: 4825741.62, x: 598648, y: 564732},
            {j: 116.369853, w: 39.912979, utm_x: 12954373.73, utm_y: 4825631.62, x: 624561, y: 578039},
            {j: 116.433552, w: 39.914694, utm_x: 12961464.75, utm_y: 4825879.53, x: 652972, y: 591348},
            {j: 116.457034, w: 39.914273, utm_x: 12964078.78, utm_y: 4825818.67, x: 663028, y: 596444},
            {j: 116.490927, w: 39.914127, utm_x: 12967851.77, utm_y: 4825797.57, x: 677968, y: 604188},
            {j: 116.483839, w: 39.877198, utm_x: 12967062.73, utm_y: 4820460.67, x: 658596, y: 610312},
            {j: 116.405777, w: 39.864461, utm_x: 12958372.82, utm_y: 4818620.62, x: 619256, y: 596088},
            {j: 116.35345 , w: 39.859774, utm_x: 12952547.74, utm_y: 4817943.6 , x: 594633, y: 585851},
            {j: 116.403818, w: 39.9141 , utm_x: 12958154.74, utm_y: 4825793.66, x: 639699, y: 585226},
            {j: 116.318111, w: 39.891101, utm_x: 12948613.78, utm_y: 4822469.56, x: 592856, y: 571480},
            {j: 116.413047, w: 39.907238, utm_x: 12959182.12, utm_y: 4824801.76, x: 640680, y: 588704},
            {j: 116.390843, w: 39.906113, utm_x: 12956710.35, utm_y: 4824639.16, x: 630620, y: 584108},
            {j: 116.446527, w: 39.899438, utm_x: 12962909.14, utm_y: 4823674.4 , x: 651752, y: 597416},
            {j: 116.388665, w: 39.95527 , utm_x: 12956467.9 , utm_y: 4831746.87, x: 650656, y: 572800},
            {j: 116.398343, w: 39.939704, utm_x: 12957545.26, utm_y: 4829495.6 , x: 648036, y: 578452},
            {j: 116.355101, w: 39.973581, utm_x: 12952731.53, utm_y: 4834395.82, x: 643268, y: 560944},
            {j: 116.380727, w: 39.88464 , utm_x: 12955584.23, utm_y: 4821535.94, x: 616920, y: 586496},
            {j: 116.360843, w: 39.946452, utm_x: 12953370.73, utm_y: 4830471.48, x: 635293, y: 568765},
            {j: 116.340955, w: 39.973421, utm_x: 12951156.79, utm_y: 4834372.67, x: 638420, y: 558632},
            {j: 116.322585, w: 40.023941, utm_x: 12949111.83, utm_y: 4841684.79, x: 652135, y: 543802},
            {j: 116.356486, w: 39.883341, utm_x: 12952885.71, utm_y: 4821348.24, x: 606050, y: 581443},
            {j: 116.339592, w: 39.992259, utm_x: 12951005.06, utm_y: 4837098.59, x: 645664, y: 554400},
            {j: 116.3778 , w: 39.86392 , utm_x: 12955258.4 , utm_y: 4818542.48, x: 606848, y: 590328},
            {j: 116.377354, w: 39.964124, utm_x: 12955208.75, utm_y: 4833027.64, x: 649911, y: 568581},
            {j: 116.361837, w: 39.963897, utm_x: 12953481.39, utm_y: 4832994.8 , x: 643286, y: 565175},
            {j: 116.441397, w: 39.939403, utm_x: 12962338.06, utm_y: 4829452.07, x: 666772, y: 587728},
            {j: 116.359176, w: 40.006631, utm_x: 12953185.16, utm_y: 4839178.78, x: 660440, y: 555411}
        ],
        sz: [
            {"w":22.498861,"utm_x":12677279.029193671,"utm_y":2555027.9501714734,"j":113.880696,"y":1104472,"x":947240},
            {"w":22.500706,"utm_x":12683920.978881944,"utm_y":2555248.973138607,"j":113.940361,"y":1122320,"x":974864},
            {"w":22.576848,"utm_x":12675897.984563945,"utm_y":2564373.058056766,"j":113.86829,"y":1074048,"x":979136},
            {"w":22.55689,"utm_x":12680064.05051775,"utm_y":2561981.0013635466,"j":113.905714,"y":1092484,"x":986240},
            {"w":22.58066,"utm_x":12678671.98513852,"utm_y":2564829.983373251,"j":113.893209,"y":1080528,"x":992088},
            {"w":22.595751,"utm_x":12678298.949465925,"utm_y":2566638.9913895614,"j":113.889858,"y":1074484,"x":997960},
            {"w":22.557499,"utm_x":12684523.001238672,"utm_y":2562053.9875916084,"j":113.945769,"y":1104696,"x":1004564},
            {"w":22.648419,"utm_x":12676422.97299485,"utm_y":2572954.0513219936,"j":113.873006,"y":1051384,"x":1015916},
            {"w":22.562664,"utm_x":12690460.958807131,"utm_y":2562673.0054078405,"j":113.99911,"y":1119860,"x":1030228},
            {"w":22.646618,"utm_x":12683008.037804369,"utm_y":2572738.0652955617,"j":113.93216,"y":1070324,"x":1041496},
            {"w":22.571091,"utm_x":12695789.992135335,"utm_y":2563683.019582462,"j":114.046981,"y":1131924,"x":1055628},
            {"w":22.704467,"utm_x":12682276.994753957,"utm_y":2579677.075645295,"j":113.925593,"y":1048536,"x":1066348},
            {"w":22.547152,"utm_x":12702917.96800879,"utm_y":2560813.9850610085,"j":114.111012,"y":1160352,"x":1072596},
            {"w":22.546192,"utm_x":12704502.952164687,"utm_y":2560698.9417545213,"j":114.12525,"y":1165256,"x":1078452},
            {"w":22.5714,"utm_x":12702350.00978689,"utm_y":2563720.0558210905,"j":114.10591,"y":1150556,"x":1081960},
            {"w":22.555004,"utm_x":12704883.001041513,"utm_y":2561754.9738317807,"j":114.128664,"y":1163304,"x":1084172},
            {"w":22.551925,"utm_x":12706255.028694374,"utm_y":2561385.978019464,"j":114.140989,"y":1168216,"x":1088116},
            {"w":22.693756,"utm_x":12690318.02302569,"utm_y":2578392.0635360866,"j":113.997826,"y":1075100,"x":1092860},
            {"w":22.573769,"utm_x":12705731.042149788,"utm_y":2564004.003107545,"j":114.136282,"y":1159404,"x":1096572},
            {"w":22.583238,"utm_x":12706369.021093281,"utm_y":2565139.002548978,"j":114.142013,"y":1157896,"x":1103632},
            {"w":22.605844,"utm_x":12704694.980375737,"utm_y":2567848.984570506,"j":114.126975,"y":1145540,"x":1107972},
            {"w":22.637228,"utm_x":12702545.043656897,"utm_y":2571612.010208761,"j":114.107662,"y":1128764,"x":1114460},
            {"w":22.62496,"utm_x":12707132.013185183,"utm_y":2570140.9407190788,"j":114.148867,"y":1145732,"x":1127028},
            {"w":22.644524,"utm_x":12707016.01701364,"utm_y":2572486.9446672536,"j":114.147825,"y":1138800,"x":1135876},
            {"w":22.640188,"utm_x":12711515.0431873,"utm_y":2571966.966986786,"j":114.18824,"y":1152692,"x":1151836},
            {"w":22.59807,"utm_x":12720011.039168343,"utm_y":2566916.995355996,"j":114.26456,"y":1191212,"x":1165180},
            {"w":22.668221,"utm_x":12714081.987256048,"utm_y":2575329.007304823,"j":114.211299,"y":1150576,"x":1175404},
            {"w":22.702591,"utm_x":12717292.031020584,"utm_y":2579452.0022288463,"j":114.240135,"y":1148204,"x":1204600},
            {"w":22.731786,"utm_x":12717795.9798388,"utm_y":2582955.0308636553,"j":114.244662,"y":1139532,"x":1220540},
            {"w":22.727494,"utm_x":12720675.957721734,"utm_y":2582439.9980541077,"j":114.270533,"y":1148992,"x":1230084},
            {"w":22.716335,"utm_x":12725500.040345404,"utm_y":2581101.0132384477,"j":114.313868,"y":1166316,"x":1244102}
        ],
        gz: [
            {j: 113.335098, w: 23.147289, utm_x: 12616542.68, utm_y: 2632892.7, x: 1129109, y: 1073920},
            {j: 113.320932, w: 23.146956, utm_x: 12614965.71, utm_y: 2632852.62, x: 1125620, y: 1071640},
            {j: 113.321435, w: 23.140119, utm_x: 12615021.7 , utm_y: 2632029.65, x: 1124032, y: 1072882},
            {j: 113.321471, w: 23.119165, utm_x: 12615025.71, utm_y: 2629507.68, x: 1118932, y: 1076530},
            {j: 113.340201, w: 23.118616, utm_x: 12617110.75, utm_y: 2629441.61, x: 1123238, y: 1079667},
            {j: 113.358068, w: 23.116323, utm_x: 12619099.71, utm_y: 2629165.66, x: 1126968, y: 1083116},
            {j: 113.357529, w: 23.131271, utm_x: 12619039.71, utm_y: 2630964.68, x: 1130508, y: 1080440},
            {j: 113.365811, w: 23.150595, utm_x: 12619961.67, utm_y: 2633290.66, x: 1137205, y: 1078567},
            {j: 113.294145, w: 23.118467, utm_x: 12611983.76, utm_y: 2629423.68, x: 1112245, y: 1072043},
            {j: 113.28615 , w: 23.121525, utm_x: 12611093.75, utm_y: 2629791.7 , x: 1110993, y: 1070197},
            {j: 113.307152, w: 23.055497, utm_x: 12613431.71, utm_y: 2621847.21, x: 1100144, y: 1085123},
            {j: 113.333445, w: 23.052687, utm_x: 12616358.66, utm_y: 2621509.2 , x: 1105784, y: 1089948},
            {j: 113.347476, w: 23.048755, utm_x: 12617920.6 , utm_y: 2621036.24, x: 1108099, y: 1093064},
            {j: 113.385774, w: 23.036574, utm_x: 12622183.96, utm_y: 2619571.12, x: 1113850, y: 1101834},
            {j: 113.364185, w: 22.89798 , utm_x: 12619780.66, utm_y: 2602910.64, x: 1073186, y: 1123374},
            {j: 113.404577, w: 22.906481, utm_x: 12624277.13, utm_y: 2603932.06, x: 1084888, y: 1128692},
            {j: 113.430856, w: 22.913156, utm_x: 12627202.52, utm_y: 2604734.12, x: 1092892, y: 1131761},
            {j: 113.384554, w: 22.933021, utm_x: 12622048.15, utm_y: 2607121.32, x: 1086975, y: 1120403},
            {j: 113.263566, w: 23.146333, utm_x: 12608579.68, utm_y: 2632777.63, x: 1111742, y: 1062098},
            {j: 113.239213, w: 23.152996, utm_x: 12605868.69, utm_y: 2633579.69, x: 1107616, y: 1056740},
            {j: 113.253865, w: 23.131628, utm_x: 12607499.76, utm_y: 2631007.65, x: 1105912, y: 1062966},
            {j: 113.240767, w: 23.088434, utm_x: 12606041.68, utm_y: 2625809.7 , x: 1092270, y: 1068184},
            {j: 113.279628, w: 23.088284, utm_x: 12610367.72, utm_y: 2625791.65, x: 1101412, y: 1074883},
            {j: 113.462271, w: 23.107058, utm_x: 12630699.66, utm_y: 2628050.7 , x: 1148752, y: 1101736},
            {j: 113.401618, w: 23.052957, utm_x: 12623947.73, utm_y: 2621541.68, x: 1121925, y: 1101535},
            {j: 113.422504, w: 23.05905 , utm_x: 12626272.77, utm_y: 2622274.61, x: 1128470, y: 1104049},
            {j: 113.362506, w: 23.107149, utm_x: 12619593.75, utm_y: 2628061.65, x: 1125835, y: 1085505},
            {j: 113.419629, w: 23.143176, utm_x: 12625952.73, utm_y: 2632397.61, x: 1148133, y: 1089052},
            {j: 113.23315 , w: 23.062251, utm_x: 12605193.75, utm_y: 2622659.67, x: 1084184, y: 1071368},
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
            {j: 121.4966 , w: 31.243614, utm_x: 13525086.81, utm_y: 3642061.58, x: 1071220, y: 1056805},
            {j: 121.485021, w: 31.26138, utm_x: 13523797.82, utm_y: 3644363.54, x: 1075708, y: 1045540},
            {j: 121.465114, w: 31.278803, utm_x: 13521581.76, utm_y: 3646621.48, x: 1073740, y: 1031268},
            {j: 121.454784, w: 31.266566, utm_x: 13520431.82, utm_y: 3645035.58, x: 1063591, y: 1033191},
            {j: 121.46851 , w: 31.24951, utm_x: 13521959.81, utm_y: 3642825.48, x: 1060200, y: 1044520},
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
    getLnglatIndex: function(city,x,y) {
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
    getOMapIndex_mm: function(city,utm_x,utm_y) {
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

    getDis: function(x,y,x1,y1) {
        return Math.abs(x - x1) + Math.abs(y - y1);
    },
    //从标准平面坐标得到地图坐标
    toMap: function(city,x,y) {
        var x2 = (x - y) * this.num[city].num;
        var y2 = (x + y) * this.num[city].num * this.num[city].num2;

        return {x: x2, y: y2};
    },
    //从地图坐标得到标准平面坐标
    fromMap: function(city,x,y) {
        y = y / this.num[city].num2;
        var x2 = (x + y) / (this.num[city].num * 2);
        var y2 = (y - x) / (this.num[city].num * 2);

        return {x: x2, y: y2};
    },
    //得到小范围地图精度
    getDgPix_mm: function(city,index0,index1) {
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
    getPx_mm: function(city,utm_x,utm_y,index0,index1) {
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
    getJw_mm: function(city,x,y,index0,index1) {
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
    ,getOMap_pts: function(city,pts) {
        return this.getOMap_index(city, pts.lng, pts.lat, pts.lt, pts.rb);
    }
    ,getMapJw_pts: function(city,pts) {
        return this.getMapJw_index(city, pts.lng, 9998336 - pts.lat, pts.lt, pts.rb);
    }
    ,getOMap_index: function(city,utm_x,utm_y,lt,rb) {
        if (!lt || !rb) {
            var index = this.getOMapIndex_mm(city, utm_x, utm_y);
        }else {
            var index = {lt: lt, rb: rb};
        }
        var xy = this.getPx_mm(city, utm_x, utm_y, index.lt, index.rb);
        return {x: Math.floor(xy.x), y: 9998336 - Math.floor(xy.y), lt: index.lt, rb: index.rb};
    }
    ,getMapJw_index: function(city,x,y,lt,rb) {
        if (!lt || !rb) {
            var index = this.getLnglatIndex(city, x, y);
        }else {
            var index = {lt: lt, rb: rb};
        }
        var lnglat = this.getJw_mm(city, x, y, index.lt, index.rb);
        return {lng: lnglat.lng, lat: lnglat.lat, lt: index.lt, rb: index.rb};
    }
});

var TD = TD || {}

TD.pointToPixel = function(point, map){
    var zoom = map.getZoom();
    var center = map.getCenter();
    var size = map.getSize()
    return TD.geo.pointToPixel(point, zoom, center, size)
}

TD.geo = {
    pointToPixel : function(point, zoom, center, size){
        return this.projection.pointToPixel(point, zoom, center, size)
    }

    ,pixelToPoint : function(piexl){

    }
    /**
     * 经纬度变换至墨卡托坐标
     * @param Point 经纬度
     * @return Point 墨卡托
     */
    ,lngLatToMercator : function(){
        return this.projection.convertLL2MC(point);
    }
}
TD.geo.projection = new MercatorProjection();
/**
 * 百度墨卡托投影类
 */
function MercatorProjection(){
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
    ,getDistanceByMC:function(point1, point2){
        if(!point1 || !point2) return 0;
        var x1,y1,x2,y2;
        point1 = this.convertMC2LL(point1);
        if(!point1) return 0;
        x1 = this.toRadians(point1.lng);
        y1 = this.toRadians(point1.lat);
        point2 = this.convertMC2LL(point2);
        if(!point2) return 0;
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
    ,getDistanceByLL:function(point1, point2){
        if(!point1 || !point2) return 0;
        point1.lng=this.getLoop(point1.lng,-180,180);
        point1.lat=this.getRange(point1.lat,-74,74);
        point2.lng=this.getLoop(point2.lng,-180,180);
        point2.lat=this.getRange(point2.lat,-74,74);
        var x1,x2,y1,y2;
        x1=this.toRadians(point1.lng);
        y1=this.toRadians(point1.lat);
        x2=this.toRadians(point2.lng);
        y2=this.toRadians(point2.lat);
        return this.getDistance(x1,x2,y1,y2);
    }
    /**
     * 平面直角坐标转换成经纬度坐标;
     * @param {Point} point 平面直角坐标
     * @return {Point} 返回经纬度坐标
     */
    ,convertMC2LL:function(point){
        var temp,factor;
        temp=new Point(Math.abs(point.lng),Math.abs(point.lat));
        for(var i=0;i<this.MCBAND.length;i++){
            if(temp.lat>=this.MCBAND[i]){
                factor=this.MC2LL[i];
                break;
            }
        };
        var lnglat=  this.convertor(point,factor);
        var point = new Point(lnglat.lng.toFixed(6),lnglat.lat.toFixed(6));
        return point;
    }

    /**
     * 经纬度坐标转换成平面直角坐标;
     * @param {Point} point 经纬度坐标
     * @return {Point} 返回平面直角坐标
     */
    ,convertLL2MC:function(point){
        var temp,factor;
        point.lng = this.getLoop(point.lng,-180,180);
        point.lat = this.getRange(point.lat,-74,74);
        temp = new Point(point.lng, point.lat);
        for(var i = 0; i < this.LLBAND.length; i ++){
            if(temp.lat >= this.LLBAND[i]){
                factor = this.LL2MC[i];
                break;
            }
        }
        if(!factor){
            for(var i = this.LLBAND.length-1; i >= 0; i--){
                if(temp.lat <= - this.LLBAND[i]){
                    factor = this.LL2MC[i];
                    break;
                }
            }
        }
        var mc = this.convertor(point, factor);
        var point = new Point(mc.lng.toFixed(2),mc.lat.toFixed(2));
        return point;
    }
    ,convertor:function(fromPoint,factor){
        if (!fromPoint || !factor){
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

    ,getDistance:function(x1,x2,y1,y2){
        return this.EARTHRADIUS*Math.acos((Math.sin(y1)*Math.sin(y2)+Math.cos(y1)*Math.cos(y2)*Math.cos(x2-x1)));
    }

    ,toRadians:function(angdeg){
        return Math.PI*angdeg/180;
    }

    ,toDegrees:function(angrad){
        return (180*angrad)/Math.PI;
    }
    ,getRange:function(v,a,b){
        if(a!=null){
            v=Math.max(v,a);
        }
        if(b!=null){
            v=Math.min(v,b);
        }
        return v
    }
    ,getLoop:function(v,a,b){
        while(v>b){
            v-=b-a
        }
        while(v<a){
            v+=b-a
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
    lngLatToMercator: function(point) {
        return MercatorProjection.convertLL2MC(point);
    },
    /**
     * 球面到平面坐标
     * @param Point 球面坐标
     * @return Pixel 平面坐标
     */
    lngLatToPoint: function(point) {
        var mercator = MercatorProjection.convertLL2MC(point);
        return new Pixel(mercator.lng, mercator.lat);
    },
    /**
     * 墨卡托变换至经纬度
     * @param Point 墨卡托
     * @returns Point 经纬度
     */
    mercatorToLngLat: function(point) {
        return MercatorProjection.convertMC2LL(point);
    },
    /**
     * 平面到球面坐标
     * @param Pixel 平面坐标
     * @returns Point 球面坐标
     */
    pointToLngLat: function(point) {
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
    pointToPixel: function(point, zoom, mapCenter, mapSize, curCity) {
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
    pixelToPoint: function(pixel, zoom, mapCenter, mapSize, curCity) {
        if (!pixel) {
            return;
        }
        var zoomUnits = this.getZoomUnits(zoom);
        var lng = mapCenter.lng + zoomUnits * (pixel.x - mapSize.width / 2);
        var lat = mapCenter.lat - zoomUnits * (pixel.y - mapSize.height / 2);
        var point = new Point(lng, lat);
        return this.mercatorToLngLat(point, curCity);
    },
    getZoomUnits: function(zoom){
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
    lngLatToMercator: function(lngLat, mapCity) {
        return this._convert2DTo3D(mapCity, MercatorProjection.convertLL2MC(lngLat));
    }
    ,mercatorToLngLat: function(mercator, mapCity) {
        return MercatorProjection.convertMC2LL(this._convert3DTo2D(mapCity, mercator));
    }
    ,lngLatToPoint: function(lngLat, mapCity) {
        var mercator = this._convert2DTo3D(mapCity, MercatorProjection.convertLL2MC(lngLat));
        return new Pixel(mercator.lng, mercator.lat);
    }
    ,pointToLngLat: function(point, mapCity) {
        var mercator = new Point(point.x, point.y);
        return MercatorProjection.convertMC2LL(this._convert3DTo2D(mapCity, mercator));
    }
    ,_convert2DTo3D: function(city, point){
        var p = CoordTrans.getOMap_pts(city || 'bj', point);
        return new Point(p.x, p.y);
    }
    ,_convert3DTo2D: function(city, point){
        var p = CoordTrans.getMapJw_pts(city || 'bj', point);
        return new Point(p.lng, p.lat);
    }
    ,getZoomUnits: function(zoom) {
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
function Pixel(x, y){
    this.x = x || 0;
    this.y = y || 0;
};

Pixel.prototype.equals = function(other){
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
Point.isInRange = function(pt) {
    return pt && pt.lng <= 180 && pt.lng >= -180 && pt.lat <= 74 && pt.lat >= -74;
}
Point.prototype.equals = function(other) {
    return other && this.lat == other.lat && this.lng == other.lng;
};

/**
 * 投影基类，抽象类不可实例化
 * @constructor
 */
function Projection(){
};

/**
 * 抽象，从球面坐标转换到平面坐标
 */
Projection.prototype.lngLatToPoint = function(){
    throw "lngLatToPoint方法未实现";
};

/**
 * 抽象，从平面坐标转换到球面坐标
 */
Projection.prototype.pointToLngLat = function(){
    throw "pointToLngLat方法未实现";
};


var window = window || self;
var TD = TD || {};
var TDMap = TDMap || {};
TDMap.projection = new MercatorProjection();
/**
 * 坐标数字对象转像素坐标数组
 * @param {Object|| Array} points
 * @return{Array} pixels
 */
TDMap.pointsToPixels = function(points, map){
    var data = points;
    points = isArray(data)? data : data.request.data;
    map = map || data.request.map;
    var pixels = [];
    for(var i=0, len = points.length;i<len; i++){
        pixels.push(TDMap.pointToPixel(points[i], map));
    }
    return pixels;
}
/**
 * 经纬度转像素
 * @param {Object} point
 * @param {Object} map
 */
TDMap.pointToPixel = function(point, map){
    var zoom = map.zoom;
    var center = map.center;
    var size = map.size;
    var size = map.size;
    var obj = TDMap.projection.pointToPixel(point, zoom, center, size);
    if(point.count){
        obj.count = point.count;
    }
    return obj;
}


var window = window || self;
var HeatOverlay = {
    pointsToPixels : function(webObj){
        var pixels = TDMap.pointsToPixels(webObj);
        TD.postMessage(pixels, webObj);
    }
}

var window = window || self;
var BoundaryOverlay = {
    calculatePixel: function (webObj) {
        var data = webObj;
        points = isArray(data) ? data : data.request.data;
        map = data.request.map;

        for (var j = 0; j < points.length; j++) {
            if (points[j].geo) {
                var tmp = [];
                for (var i = 0; i < points[j].geo.length; i++) {
                    var pixel = TDMap.pointToPixel(new Point(points[j].geo[i][0], points[j].geo[i][1]), map);
                    tmp.push([pixel.x, pixel.y, parseFloat(points[j].geo[i][2])]);
                }
                points[j].pgeo = tmp;
            }
        }

        //var pixels = TDMap.pointsToPixels(webObj);
        TD.postMessage(points, webObj);
    }
}

var window = window || self;
var GriddingOverlay = {
    toRecGrids: function (webObj) {
        var data = webObj;
        points = data.request.data.points,
            zoomUnit = data.request.data.zoomUnit,
            size = data.request.data.size,
            mapSize = data.request.data.mapSize,
            mapCenter = data.request.data.mapCenter;
        nwMc = data.request.data.nwMc,
            map = data.request.map,
            zoom = data.request.data.zoom,
            griddingType = data.request.data.griddingType;  //聚合方式  累加权重  平均权重


        var data = GriddingOverlay._calculatePixel(map, points, mapSize, mapCenter, zoom);
        //var obj = {
        //    data: points,
        //    nwMc: nwMc,
        //    size: size,
        //    zoomUnit: zoomUnit,
        //    mapSize: mapSize,
        //    mapCenter: mapCenter
        //};
        var gridsObj = null;
        if (griddingType === "avg") {
            gridsObj = GriddingOverlay.recGrids(points, map, nwMc, size, zoomUnit, mapSize, mapCenter);
        } else if (griddingType === "sum") {
            gridsObj = GriddingOverlay.recGrids2(points, map, nwMc, size, zoomUnit, mapSize, mapCenter);
        }


        TD.postMessage(gridsObj, webObj);
    },
    _calculatePixel: function (map, data, mapSize, mapCenter, zoom) {

        var zoomUnit = Math.pow(2, 18 - zoom);
        var mcCenter = TDMap.projection.lngLatToPoint(mapCenter);

        var nwMc = new Pixel(mcCenter.x - mapSize.width / 2 * zoomUnit, mcCenter.y + mapSize.height / 2 * zoomUnit); //左上角墨卡托坐标
        for (var j = 0; j < data.length; j++) {
            if (data[j].lng && data[j].lat && !data[j].x && !data[j].y) {
                var pixel = TDMap.projection.lngLatToPoint(new Point(data[j].lng, data[j].lat), map);
                data[j].x = pixel.x;
                data[j].y = pixel.y;

            }
            if (data[j].x && data[j].y) {
                data[j].px = (data[j].x - nwMc.x) / zoomUnit;
                data[j].py = (nwMc.y - data[j].y) / zoomUnit;
            }

        }
        return data;
    },
    recGrids2: function (data, map, nwMc, size, zoomUnit, mapSize, mapCenter) {
        //isAvg 聚合的方式
        var max = 0;
        var min = 0;

        var grids = {};

        var gridStep = size / zoomUnit;

        var startXMc = parseInt(nwMc.x / size, 10) * size;

        var startX = (startXMc - nwMc.x) / zoomUnit;

        var stockXA = [];
        var stickXAIndex = 0;
        while (startX + stickXAIndex * gridStep < mapSize.width) {
            var value = startX + stickXAIndex * gridStep;
            stockXA.push(value.toFixed(2));
            stickXAIndex++;
        }

        var startYMc = parseInt(nwMc.y / size, 10) * size + size;
        var startY = (nwMc.y - startYMc) / zoomUnit;
        var stockYA = [];
        var stickYAIndex = 0;
        while (startY + stickYAIndex * gridStep < mapSize.height) {
            value = startY + stickYAIndex * gridStep;
            stockYA.push(value.toFixed(2));
            stickYAIndex++;
        }

        for (var i = 0; i < stockXA.length; i++) {
            for (var j = 0; j < stockYA.length; j++) {
                var name = stockXA[i] + '_' + stockYA[j];
                grids[name] = 0;
            }
        }

        for (var i = 0; i < data.length; i++) {
            var x = data[i].px;
            var y = data[i].py;
            var val = data[i].count;

            for (var j = 0; j < stockXA.length; j++) {
                var dataX = Number(stockXA[j]);
                if (x >= dataX && x < dataX + gridStep) {
                    for (var k = 0; k < stockYA.length; k++) {
                        var dataY = Number(stockYA[k]);
                        if (y >= dataY && y < dataY + gridStep) {
                            grids[stockXA[j] + '_' + stockYA[k]] += val;
                            val = grids[stockXA[j] + '_' + stockYA[k]];

                        }
                    }
                }
            }
            min = min || val;
            max = max || val;
            min = min > val ? val : min;
            max = max < val ? val : max;
        }


        return {
            grids: grids,
            max: max,
            min: 0
        };
    },
    recGrids: function (data, map, nwMc, size, zoomUnit, mapSize, mapCenter) {
        //isAvg 聚合的方式
        var max = 0;
        var min = 0;

        var grids = {};

        var gridStep = size / zoomUnit;

        var startXMc = parseInt(nwMc.x / size, 10) * size;

        var startX = (startXMc - nwMc.x) / zoomUnit;

        var stockXA = [];
        var stickXAIndex = 0;
        while (startX + stickXAIndex * gridStep < mapSize.width) {
            var value = startX + stickXAIndex * gridStep;
            stockXA.push(value.toFixed(2));
            stickXAIndex++;
        }

        var startYMc = parseInt(nwMc.y / size, 10) * size + size;
        var startY = (nwMc.y - startYMc) / zoomUnit;
        var stockYA = [];
        var stickYAIndex = 0;
        while (startY + stickYAIndex * gridStep < mapSize.height) {
            value = startY + stickYAIndex * gridStep;
            stockYA.push(value.toFixed(2));
            stickYAIndex++;
        }

        for (var i = 0; i < stockXA.length; i++) {
            for (var j = 0; j < stockYA.length; j++) {
                var name = stockXA[i] + '_' + stockYA[j];
                grids[name] = [];
            }
        }

        for (var i = 0; i < data.length; i++) {
            var x = data[i].px;
            var y = data[i].py;
            var val = data[i].count;

            for (var j = 0; j < stockXA.length; j++) {
                var dataX = Number(stockXA[j]);
                if (x >= dataX && x < dataX + gridStep) {
                    for (var k = 0; k < stockYA.length; k++) {
                        var dataY = Number(stockYA[k]);
                        if (y >= dataY && y < dataY + gridStep) {
                            grids[stockXA[j] + '_' + stockYA[k]].push(val);

                        }
                    }
                }
            }
        }
        for (var o in grids) {
            var arr = grids[o], all = 0;
            if (arr.length > 0) {
                for (var i = 0; i < arr.length; i++) {
                    all += arr[i];
                }
                grids[o] = all / arr.length;
                if (grids[o] > max) {
                    max = grids[o];
                }
            } else {
                grids[o] = 0;
            }


        }

        return {
            grids: grids,
            max: max,
            min: 0
        };
    }
};

var window = window || self;
var GriddingOverlay2 = {
    toRecGrids: function (webObj) {
        var data = webObj;
        points = data.request.data.points,
            zoomUnit = data.request.data.zoomUnit,
            size = data.request.data.size,
            mapSize = data.request.data.mapSize,
            mapCenter = data.request.data.mapCenter;
        nwMc = data.request.data.nwMc,
            map = data.request.map,
            zoom = data.request.data.zoom,
            griddingType = data.request.data.griddingType;  //聚合方式  累加权重  平均权重


        var data = GriddingOverlay2._calculatePixel(map, points, mapSize, mapCenter, zoom);
        //var obj = {
        //    data: points,
        //    nwMc: nwMc,
        //    size: size,
        //    zoomUnit: zoomUnit,
        //    mapSize: mapSize,
        //    mapCenter: mapCenter
        //};
        var gridsObj = null;
        if (griddingType === "avg") {
            gridsObj = GriddingOverlay2.recGrids(points, map, nwMc, size, zoomUnit, mapSize, mapCenter);
        } else if (griddingType === "sum") {
            gridsObj = GriddingOverlay2.recGrids2(points, map, nwMc, size, zoomUnit, mapSize, mapCenter);
        }


        TD.postMessage(gridsObj, webObj);
    },
    _calculatePixel: function (map, data, mapSize, mapCenter, zoom) {

        var zoomUnit = Math.pow(2, 18 - zoom);
        var mcCenter = TDMap.projection.lngLatToPoint(mapCenter);

        var nwMc = new Pixel(mcCenter.x - mapSize.width / 2 * zoomUnit, mcCenter.y + mapSize.height / 2 * zoomUnit); //左上角墨卡托坐标
        for (var j = 0; j < data.length; j++) {
            if (data[j].lng && data[j].lat && !data[j].x && !data[j].y) {
                var pixel = TDMap.projection.lngLatToPoint(data[j], map);
                data[j].x = pixel.x;
                data[j].y = pixel.y;

            }
            if (data[j].x && data[j].y) {
                data[j].px = (data[j].x - nwMc.x) / zoomUnit;
                data[j].py = (nwMc.y - data[j].y) / zoomUnit;
            }

        }
        return data;
    },
    recGrids2: function (data, map, nwMc, size, zoomUnit, mapSize, mapCenter) {
        //isAvg 聚合的方式
        var max = 0;
        var min = 0;

        var grids = {};

        var gridStep = size / zoomUnit;

        var startXMc = parseInt(nwMc.x / size, 10) * size;

        var startX = (startXMc - nwMc.x) / zoomUnit;

        var stockXA = [];
        var stickXAIndex = 0;
        while (startX + stickXAIndex * gridStep < mapSize.width) {
            var value = startX + stickXAIndex * gridStep;
            stockXA.push(value.toFixed(2));
            stickXAIndex++;
        }

        var startYMc = parseInt(nwMc.y / size, 10) * size + size;
        var startY = (nwMc.y - startYMc) / zoomUnit;
        var stockYA = [];
        var stickYAIndex = 0;
        while (startY + stickYAIndex * gridStep < mapSize.height) {
            value = startY + stickYAIndex * gridStep;
            stockYA.push(value.toFixed(2));
            stickYAIndex++;
        }

        for (var i = 0; i < stockXA.length; i++) {
            for (var j = 0; j < stockYA.length; j++) {
                var name = stockXA[i] + '_' + stockYA[j];
                grids[name] = [];
            }
        }

        for (var i = 0; i < data.length; i++) {
            var x = data[i].px;
            var y = data[i].py;
            //var val = data[i].count;

            for (var j = 0; j < stockXA.length; j++) {
                var dataX = Number(stockXA[j]);
                if (x >= dataX && x < dataX + gridStep) {
                    for (var k = 0; k < stockYA.length; k++) {
                        var dataY = Number(stockYA[k]);
                        if (y >= dataY && y < dataY + gridStep) {
                            grids[stockXA[j] + '_' + stockYA[k]].push(data[i]);
                            //   val = grids[stockXA[j] + '_' + stockYA[k]];

                        }
                    }
                }
            }

        }


        return {
            grids: grids

        };
    },
    recGrids: function (data, map, nwMc, size, zoomUnit, mapSize, mapCenter) {
        //isAvg 聚合的方式
        var max = 0;
        var min = 0;

        var grids = {};

        var gridStep = size / zoomUnit;

        var startXMc = parseInt(nwMc.x / size, 10) * size;

        var startX = (startXMc - nwMc.x) / zoomUnit;

        var stockXA = [];
        var stickXAIndex = 0;
        while (startX + stickXAIndex * gridStep < mapSize.width) {
            var value = startX + stickXAIndex * gridStep;
            stockXA.push(value.toFixed(2));
            stickXAIndex++;
        }

        var startYMc = parseInt(nwMc.y / size, 10) * size + size;
        var startY = (nwMc.y - startYMc) / zoomUnit;
        var stockYA = [];
        var stickYAIndex = 0;
        while (startY + stickYAIndex * gridStep < mapSize.height) {
            value = startY + stickYAIndex * gridStep;
            stockYA.push(value.toFixed(2));
            stickYAIndex++;
        }

        for (var i = 0; i < stockXA.length; i++) {
            for (var j = 0; j < stockYA.length; j++) {
                var name = stockXA[i] + '_' + stockYA[j];
                grids[name] = [];
            }
        }

        for (var i = 0; i < data.length; i++) {
            var x = data[i].px;
            var y = data[i].py;
            var val = data[i].count;

            for (var j = 0; j < stockXA.length; j++) {
                var dataX = Number(stockXA[j]);
                if (x >= dataX && x < dataX + gridStep) {
                    for (var k = 0; k < stockYA.length; k++) {
                        var dataY = Number(stockYA[k]);
                        if (y >= dataY && y < dataY + gridStep) {
                            grids[stockXA[j] + '_' + stockYA[k]].push(val);

                        }
                    }
                }
            }
        }
        for (var o in grids) {
            var arr = grids[o], all = 0;
            if (arr.length > 0) {
                for (var i = 0; i < arr.length; i++) {
                    all += arr[i];
                }
                grids[o] = all / arr.length;
                if (grids[o] > max) {
                    max = grids[o];
                }
            } else {
                grids[o] = 0;
            }


        }

        return {
            grids: grids,
            max: max,
            min: 0
        };
    }
};

var window = window || self;
var HoneycombOverlay = {
    toRecGrids: function (webObj) {
        var data = webObj;
        points = data.request.data.points,
            zoomUnit = data.request.data.zoomUnit,
            size = data.request.data.size,
            mapSize = data.request.data.mapSize,
            mapCenter = data.request.data.mapCenter;
        nwMc = data.request.data.nwMc,
            map = data.request.map,
            zoom = data.request.data.zoom;

        var data = HoneycombOverlay._calculatePixel(map, points, mapSize, mapCenter, zoom);

        var gridsObj = HoneycombOverlay.honeycombGrid(points, map, nwMc, size, zoomUnit, mapSize, mapCenter);

        TD.postMessage(gridsObj, webObj);
    },
    _calculatePixel: function (map, data, mapSize, mapCenter, zoom) {

        var zoomUnit = Math.pow(2, 18 - zoom);
        var mcCenter = TDMap.projection.lngLatToPoint(mapCenter);

        var nwMc = new Pixel(mcCenter.x - mapSize.width / 2 * zoomUnit, mcCenter.y + mapSize.height / 2 * zoomUnit); //左上角墨卡托坐标
        for (var j = 0; j < data.length; j++) {
            if (data[j].lng && data[j].lat && !data[j].x && !data[j].y) {
                var pixel = TDMap.projection.lngLatToPoint(new Point(data[j].lng, data[j].lat), map);
                data[j].x = pixel.x;
                data[j].y = pixel.y;

            }
            if (data[j].x && data[j].y) {
                data[j].px = (data[j].x - nwMc.x) / zoomUnit;
                data[j].py = (nwMc.y - data[j].y) / zoomUnit;
            }

        }
        return data;
    },
    honeycombGrid: function (data, map, nwMc, size, zoomUnit, mapSize, mapCenter) {

        var max;
        var min;

        var grids = {};

        var gridStep = size / zoomUnit;

        var depthX = gridStep;
        var depthY = gridStep * 3 / 4;

        var sizeY = 2 * size * 3 / 4;
        var startYMc = parseInt(nwMc.y / sizeY + 1, 10) * sizeY;
        var startY = (nwMc.y - startYMc) / zoomUnit;
        startY = parseInt(startY, 10);

        var startXMc = parseInt(nwMc.x / size, 10) * size;
        var startX = (startXMc - nwMc.x) / zoomUnit;
        startX = parseInt(startX, 10);

        var endX = parseInt( mapSize.width + depthX, 10);
        var endY = parseInt(mapSize.height + depthY, 10);

        var pointX = startX;
        var pointY = startY;

        var odd = false;
        while (pointY < endY) {
            while (pointX < endX) {
                var x = odd ? pointX - depthX / 2 : pointX;
                x = parseInt(x, 10);
                grids[x + '|' + pointY] = grids[x + '|' + pointY] || {
                        x: x,
                        y: pointY,
                        len: 0
                    };

                pointX += depthX;
            }
            odd = !odd;
            pointX = startX;
            pointY += depthY;
        }

        for (var i in data) {
            var count = data[i].count;
            var pX = data[i].px;
            var pY = data[i].py;

            var fixYIndex = Math.round((pY - startY) / depthY);
            var fixY = fixYIndex * depthY + startY;
            var fixXIndex = Math.round((pX - startX) / depthX);
            var fixX = fixXIndex * depthX + startX;

            if (fixYIndex % 2) {
                fixX = fixX - depthX / 2;
            }
            if (fixX < startX || fixX > endX || fixY < startY || fixY > endY) {
                continue;
            }

            if (grids[fixX + '|' + fixY]) {
                grids[fixX + '|' + fixY].len += count;
                var num = grids[fixX + '|' + fixY].len;
                max = max || num;
                min = min || num;
                max = Math.max(max, num);
                min = Math.min(min, num);
            }
        }

        return {
            grids: grids,
            max: max,
            min: min
        };
    }


};

/**
 * Created by tendcloud on 2016/2/15.
 */
var window = window || self;
var PointAggregations = {
    toRecGrids: function (webObj) {
        var data = webObj;
        points = data.request.data.points,
            zoomUnit = data.request.data.zoomUnit,
            size = data.request.data.size,
            mapSize = data.request.data.mapSize,
            mapCenter = data.request.data.mapCenter;
        nwMc = data.request.data.nwMc,
            map = data.request.map,
            zoom = data.request.data.zoom;

        var data = PointAggregations._calculatePixel(map, points, mapSize, mapCenter, zoom);

        var gridsObj = PointAggregations.recGrids(points, map, nwMc, size, zoomUnit, mapSize, mapCenter);

        TD.postMessage(gridsObj, webObj);
    },
    _calculatePixel: function (map, data, mapSize, mapCenter, zoom) {

        var zoomUnit = Math.pow(2, 18 - zoom);
        var mcCenter = TDMap.projection.lngLatToPoint(mapCenter);

        var nwMc = new Pixel(mcCenter.x - mapSize.width / 2 * zoomUnit, mcCenter.y + mapSize.height / 2 * zoomUnit); //左上角墨卡托坐标
        for (var j = 0; j < data.length; j++) {
            if (data[j].lng && data[j].lat && !data[j].x && !data[j].y) {
                var pixel = TDMap.projection.lngLatToPoint(new Point(data[j].lng, data[j].lat), map);
                data[j].x = pixel.x;
                data[j].y = pixel.y;

            }
            if (data[j].x && data[j].y) {
                data[j].px = (data[j].x - nwMc.x) / zoomUnit;
                data[j].py = (nwMc.y - data[j].y) / zoomUnit;
            }

        }
        return data;
    },
    recGrids: function (data, map, nwMc, size, zoomUnit, mapSize, mapCenter) {
        var max = 0;
        var min = 0;

        var grids = {};

        var gridStep = size / zoomUnit;

        var startXMc = parseInt(nwMc.x / size, 10) * size;

        var startX = (startXMc - nwMc.x) / zoomUnit;

        var stockXA = [];
        var stickXAIndex = 0;
        while (startX + stickXAIndex * gridStep < mapSize.width) {
            var value = startX + stickXAIndex * gridStep;
            stockXA.push(value.toFixed(2));
            stickXAIndex++;
        }

        var startYMc = parseInt(nwMc.y / size, 10) * size + size;
        var startY = (nwMc.y - startYMc) / zoomUnit;
        var stockYA = [];
        var stickYAIndex = 0;
        while (startY + stickYAIndex * gridStep < mapSize.height) {
            value = startY + stickYAIndex * gridStep;
            stockYA.push(value.toFixed(2));
            stickYAIndex++;
        }

        for (var i = 0; i < stockXA.length; i++) {
            for (var j = 0; j < stockYA.length; j++) {
                var name = stockXA[i] + '_' + stockYA[j];
                grids[name] = 0;
            }
        }

        for (var i = 0; i < data.length; i++) {
            var x = data[i].px;
            var y = data[i].py;
            var val = data[i].count;

            for (var j = 0; j < stockXA.length; j++) {
                var dataX = Number(stockXA[j]);
                if (x >= dataX && x < dataX + gridStep) {
                    for (var k = 0; k < stockYA.length; k++) {
                        var dataY = Number(stockYA[k]);
                        if (y >= dataY && y < dataY + gridStep) {
                            grids[stockXA[j] + '_' + stockYA[k]] += val;
                            val = grids[stockXA[j] + '_' + stockYA[k]];

                        }
                    }
                }
            }
            min = min || val;
            max = max || val;
            min = min > val ? val : min;
            max = max < val ? val : max;
        }


        return {
            grids: grids,
            max: max,
            min: min
        };
    }
};