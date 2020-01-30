var map,plateOverlay,heatOverlay;
// 显示名称和对应的标签数据
//城市数据
var cityData = {
    curr: {cityCode: 430700, name: '常德市', bg: '#FF5722'},
    list: [
        {
            cityCode: 430200,
            name: '株洲市',
            bg: '#FFB800'
        },
        {
            cityCode: 430700,
            name: '常德市',
            bg: '#FF5722'
        },
        {
            cityCode: 430400,
            name: '衡阳市',
            bg: '#01AAED'
        },
        {
            cityCode: 430500,
            name: '邵阳市',
            bg: '#2F4056'
        },
        {
            cityCode: 430600,
            name: '岳阳市',
            bg: '#3A8302'
        },
        {
            cityCode: 430100,
            name: '长沙市',
            bg: '#783723'
        }
    ]
};

//人口数据
var aggregationData = {
    currType: "month",
    startTime: "",
    endTime: "",
    cache: {}
}

var queryMode = "time-mark";

var queryStatus = 0;
var sliderInitStatus = false;

var echartMap = {
    series: null,
    myChart: null
};

layui.use(['jquery', 'form', 'laydate', 'util'], function() {
    var $ = layui.jquery,
        laydate = layui.laydate,
        util = layui.util,
        form = layui.form;

    $(function () {
        //初始化map对象
        initMap();
        renderTimeSelect();

        setTime();
        renderCitySelect();

        getQueryParamsFromCookie();
        queryAll();
    })

    $("#queryMode").click(function(){
        if($(this).find(".fa-calendar").length==1){
            queryMode = "time-mark";
        }else{
            queryMode = "time-range";
        }

        queryModeRender();
    })

    $("#startTime").click(function(){
        if($("#timeSelect").css("display")=="none"){
            $("#timeSelect").show();
        }else{
            $("#timeSelect").hide();
        }
    });

    $("#endTime").click(function(){
        if($("#timeSelect").css("display")=="none"){
            $("#timeSelect").show();
        }else{
            $("#timeSelect").hide();
        }
    });

    $("#confirmTimeSelectBtn").click(function(){
        $("#startTime").val(aggregationData.startTime);
        $("#endTime").val(aggregationData.endTime);

        $("#timeSelect").hide();

        queryAll();
    })

    $("#hideTimeSelectBtn").click(function(){$("#timeSelect").hide()})

    //监听城市选择
    form.on("select(selectCity)", function(params){

        renderCitySelect(params.value);
        queryAll();
    })

    function initMap() {
        var dom = document.getElementById("bmap");
        echartMap.myChart = echarts.init(dom);

        echartMap.myChart.setOption({
            bmap: {
                center: [113.639913, 27.166587],// 中心位置坐标
                map: "株洲",
                zoom: 11,
                roam: true,
                show: true
            },
            tooltip: {
                show: true,
                trigger: 'item'
            },
            series: [],
        });

        var ecModel = echartMap.myChart._model;
        ecModel.eachComponent('bmap', function (bmapModel) {
            if (map == null) {
                map = bmapModel.__bmap;//由echart实例获取百度地图的实例
            }
        });

        //enableMapClick false 禁用兴趣点点击事件
        // map = new BMap.Map('map', {enableMapClick:false});
        map.centerAndZoom(new BMap.Point(113.639913, 27.166587), 12);  // 初始化地图,设置中心点坐标和地图级别
        map.addControl(new BMap.MapTypeControl());   //添加地图类型控件
        map.addControl(new BMap.ScaleControl());
        map.setCurrentCity("株洲");          // 设置地图显示的城市 此项是必须设置的
        map.enableScrollWheelZoom(true);     //开启鼠标滚轮缩放
        map.disableDoubleClickZoom();        //禁用双击放大

        // map.setMapStyle({styleJson: mapStyle});
        var opt = new BMap.NavigationControl({
            anchor: BMAP_ANCHOR_BOTTOM_LEFT,
            type: BMAP_NAVIGATION_CONTROL_LARGE
        });
        map.addControl(opt);
    }

    //查询所有数据
    function queryAll(){
        queryStatus = 0;
        queryPlate(cityData.curr.cityCode);
        queryAggregation(cityData.curr.cityCode, aggregationData.startTime, aggregationData.endTime);
    }

    // 初始化每个板块,确定其围栏范围和相关操作
    function queryPlate(cityCode) {
        //清空之前渲染的板块
        if(plateOverlay!=null){
            $.each(plateOverlay, function(ind, ply){
                map.removeOverlay(ply);
            })
        }

        layer.load(2);

        $.ajax({
            type: 'GET',
            url: "plate/info",
            data: {"cityCode": cityCode},
            success: function (data) {
                querySuccessCallback();
                if (data.status != 200) {
                    return;
                }

                renderPlate(data.result);
            },
            error: function(data){
                querySuccessCallback();
            }
        })
    };//end queryPlate

    //渲染板块
    function renderPlate(data) {
        var pointArray = [];

        //遍历数据集合
        for (var i in data) {
            (function () {
                var feature = data[i];

                //遍历圈块集合
                for (var k = 0; k < feature.geometry.coordinates.length; k++) {

                    var enclosurePoints = [];

                    for (var j = 0; j < feature.geometry.coordinates[k].length - 1; j++) {
                        var xy = feature.geometry.coordinates[k][j];
                        var point = new BMap.Point(xy[0], xy[1]);
                        enclosurePoints.push(point);
                    }


                    // 百度地图的多边形对象
                    var ply = new BMap.Polygon(enclosurePoints, {
                        strokeWeight: 1,
                        strokeColor: "#FC6D26",
                        strokeOpacity: 0.8,
                        fillColor: "#FC6D26",
                        fillOpacity: 0.4
                    });

                    pointArray = pointArray.concat(ply.getPath());
                    map.addOverlay(ply);

                    //判断是否为空，为空则初始化数组
                    if (plateOverlay == null) {
                        plateOverlay = [];
                    }

                    plateOverlay.push(ply);
                }

            })();
        }

        map.setViewport(pointArray);
        zIndexReset();
    }

    function renderCitySelect(cityCode){
        if(cityCode!=null){
            $.each(cityData.list, function(ind, city){
                if(city.cityCode==cityCode){
                    cityData.curr = city;

                    return false;
                }
            })
        }

        var selectElem = $("select[name=city]");
        selectElem.empty();
        $.each(cityData.list, function(ind, city){
            selectElem.append("<option value=\"" + city.cityCode + "\">" + city.name + "</option>");
        })
        selectElem.val(cityData.curr.cityCode);

        form.render();

        var displayElem = selectElem.parent(".layui-input-inline").find(".layui-select-title input");
        displayElem.css("color", cityData.curr.bg);

        var ddElems = selectElem.parent(".layui-input-inline").find(".layui-anim dd");

        $.each(ddElems, function(ind, ddElem){
            var value = $(ddElem).attr("lay-value");
            var bg;
            $.each(cityData.list, function(jnd, city){
                if(value == city.cityCode){
                    bg = city.bg;
                    return false;
                }
            })

            $(ddElem).css("color", bg);
        })
    }

    function setTime(startTime, endTime){
        //时间
        if(endTime==null||endTime==""){
            endTime = util.toDateString(new Date(), "yyyy-MM-dd 00");
        }
        if(startTime==null||startTime==""){
            var date = new Date();
            date.setDate(date.getDate()-1);
            startTime = util.toDateString(date, "yyyy-MM-dd 00");
        }

        $("#startTime").val(startTime);
        $("#endTime").val(endTime);
        $("#startTimeSelect").val(startTime);
        $("#endTimeSelect").val(startTime);

        aggregationData.startTime = startTime;
        aggregationData.endTime = endTime;

        form.render();
    }

    //选择默认时间
    window.selectDefaultTime = function(type){
        var date = new Date();
        var startTime;
        var endTime = util.toDateString(date, "yyyy-MM-dd 00");
        if(type=="month"){
            date.setMonth(date.getMonth()-1);
        }else if(type=="week"){
            date.setDate(date.getDate()-6);
        }else{
            return;
        }

        startTime = util.toDateString(date, "yyyy-MM-dd 00");

        setTime(startTime, endTime);
        renderCitySelect();

        queryAll();

        $("#timeSelect").hide();
    }

    //渲染时间选择列表
    function renderTimeSelect(){
        laydate.render({
            elem: '#startTimeSelect',
            position: "static",
            value: aggregationData.startTime,
            isInitValue: true,
            type: "datetime",
            format: "yyyy-MM-dd HH",
            btns: ['clear', 'now', 'confirm'],
            done: function(value, date){
                aggregationData.startTime = value;
                $("#startTime").val(value);
            }
        });

        laydate.render({
            elem: '#endTimeSelect',
            position: "static",
            value: aggregationData.endTime,
            isInitValue: true,
            type: "datetime",
            format: "yyyy-MM-dd HH",
            btns: ['clear', 'now', 'confirm'],
            done: function(value, date){
                aggregationData.endTime = value;
                $("#endTime").val(value);
            }
        });
    }

    //查询人流数据
    function queryAggregation(cityCode, startTime, endTime){
        //清空数据
        renderHeatOverlay([]);
        layer.load(2);

        var queryStr = cityCode + " " + startTime + " " + endTime;
        var cacheData = aggregationData.cache[queryStr];

        if(cacheData!=null){
            querySuccessCallback();
            renderHeatOverlay(cacheData);

            return;
        }

        $.ajax({
            type: "GET",
            url: "aggregationData/queryByParams",
            data: {"cityCode": cityCode, type: "hours", fromHoursDataTime: startTime, toHoursDataTime: endTime},
            success: function(data){
                querySuccessCallback();
                if (data.status != 200) {
                    return;
                }

                if(data.result==null){
                    data.result = [];
                }

                aggregationData.cache[queryStr] = data.result;
                renderHeatOverlay(data.result);
            },
            error: function(data){
                querySuccessCallback();
            }
        })
    }

    function querySuccessCallback(){
        queryStatus++;
        if(queryStatus>1){
            layer.closeAll('loading');
        }

        saveQueryParamsToCookie();
    }

    function renderHeatOverlay(data){
        if(heatOverlay==null){
            var overlay = new TDMap.HeatOverlay();
            map.addOverlay(overlay);
            overlay.setPoints(data);
            overlay.setOptions({
                maxValue: 5,
                radius: 20,
                maxOpacity: 0.5,
                gradient: {
                    0.25: "rgb(0,0,255)",
                    0.55: "rgb(0,255,0)",
                    0.85: "yellow",
                    1.0: "rgb(255,0,0)"
                }
            });

            heatOverlay = overlay;
            zIndexReset();
        }else{
            heatOverlay.setPoints(data);
        }
    }

    //层次重置
    function zIndexReset(){
        if($("#bmap").find('svg[type="system"]').length==0){
            setTimeout(function(){
                zIndexReset();
            }, 100);
            return;
        }
        $("#bmap").find('svg[type="system"]').parent().css({zIndex: 199});
        $("#bmap").children(".ec-extension-bmap").children("div").eq(0).children("div").eq(1).children("div").eq(3).children("div").css({zIndex: 1});
        if($("#bmap").children(".ec-extension-bmap").children("div").eq(0).children("div").eq(1).children("div").eq(3).children("canvas").length>1){
            $("#bmap").children(".ec-extension-bmap").children("div").eq(0).children("div").eq(1).children("div").eq(3).children("canvas").eq(0).remove();
        }
    }

    var cookieName = "_queryParams";

    //从cookie中获取查询参数
    function getQueryParamsFromCookie(){
        var dataStr = getCookie(cookieName);
        if(dataStr!=null&&dataStr!=""){
            var data = JSON.parse(dataStr);
            setTime(data.startTime, data.endTime);
            renderCitySelect(data.cityCode);
            queryMode = data.queryMode;
            queryModeRender();
        }
    }

    //保存查询参数到cookie
    function saveQueryParamsToCookie(){
        var data = {
            "cityCode": cityData.curr.cityCode,
            "startTime": aggregationData.startTime,
            "endTime": aggregationData.endTime,
            "queryMode": queryMode
        }

        var dataStr = JSON.stringify(data);
        //保存30天
        setCookie(cookieName, dataStr, 30);
    }

    //设置cookie
    function setCookie(cname, cvalue, exdays) {
        var d = new Date();
        d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
        var expires = "expires=" + d.toUTCString();
        document.cookie = cname + "=" + cvalue + "; " + expires;
    }

    //获取cookie
    function getCookie(cname) {
        var name = cname + "=";
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) == ' ') c = c.substring(1);
            if (c.indexOf(name) != -1) return c.substring(name.length, c.length);
        }
        return "";
    }

    function queryModeRender(){
        var elem = $("#queryMode");
        if(queryMode == "time-mark"){
            $(elem).addClass("layui-bg-orange").removeClass("layui-bg-blue");
            $(elem).find(".fa").removeClass("fa-calendar").addClass("fa-dot-circle-o");
            $("div[mode=time-mark]").show(300);
            $("div[mode=time-range]").hide();

            if(!sliderInitStatus){
                sliderInit();
                sliderInitStatus = true;
            }

            var dateStr = $("div[mode=time-mark]").find(".time-mark-active").children(".time-data").text();
            var initStartTime = dateStr + " 00";
            var initEndTime = dateStr + " 23";
            aggregationData.startTime = initStartTime;
            aggregationData.endTime = initEndTime;
        }else if(queryMode == "time-range"){
            $(elem).removeClass("layui-bg-orange").addClass("layui-bg-blue");
            $(elem).find(".fa").addClass("fa-calendar").removeClass("fa-dot-circle-o");
            $("div[mode=time-range]").show(300);
            $("div[mode=time-mark]").hide();

            aggregationData.startTime = $("#startTime").val();
            aggregationData.endTime = $("#endTime").val();
        }

        queryAggregation(cityData.curr.cityCode, aggregationData.startTime, aggregationData.endTime);
    }

    //滑块初始化
    function sliderInit(){
        var date = new Date();
        var timeMarkElems = $(".time-mark");
        date.setDate(date.getDate()-7);
        $.each(timeMarkElems, function(ind, elem){
            date.setDate(date.getDate()+1);
            $(elem).children(".time-mark-text").text(util.toDateString(date, "MM-dd"));
            $(elem).children(".time-data").text(util.toDateString(date, "yyyy-MM-dd"));
        })

        $(".time-mark").last().addClass("time-mark-active");

        $( "#timeSlider" ).slider({
            value:7,
            min: 1,
            max: 7,
            step: 1,
            slide: function( event, ui ) {
                $(".time-mark").removeClass("time-mark-active");
                var currTimeMarkElem = $(".time-mark").eq(ui.value-1);
                currTimeMarkElem.addClass("time-mark-active");

                var date = currTimeMarkElem.children(".time-data").text();
                var startTime = date + " 00";
                var endTime = date + " 23";

                aggregationData.startTime = startTime;
                aggregationData.endTime = endTime;
                queryAggregation(cityData.curr.cityCode, startTime, endTime);
            }
        });
    }

    //清除cookie
    function clearCookie(name) {
        setCookie(name, "", -1);
    }
})