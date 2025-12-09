import os

html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Global Flight Analysis</title>
    <style>
        body { background: #080808; margin: 0; overflow: hidden; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
        canvas { display: block; }
        #ui-layer { 
            position: absolute; top: 30px; left: 30px; pointer-events: none;
            background: rgba(0, 0, 0, 0.7); padding: 20px; border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(5px);
        }
        h1 { margin: 0 0 10px 0; font-size: 18px; color: #fff; text-transform: uppercase; letter-spacing: 2px; }
        .metric { display: flex; align-items: center; margin-bottom: 8px; font-size: 12px; color: #ccc; }
        .color-box { width: 12px; height: 12px; margin-right: 10px; border-radius: 2px; }
        .legend-gradient {
            width: 100%; height: 8px; margin: 5px 0;
            background: linear-gradient(to right, #4facfe, #00f2fe, #f093fb, #f5576c);
            border-radius: 4px;
        }
        .legend-labels { display: flex; justify-content: space-between; font-size: 10px; color: #888; }
    </style>
</head>
<body>
    <div id="ui-layer">
        <h1>Flight Network Analysis</h1>
        
        <div style="margin-top: 15px; margin-bottom: 5px; font-size: 11px; color: #aaa; text-transform: uppercase;">Node Size (Degree Centrality)</div>
        <div class="metric"><div class="color-box" style="background: rgba(255, 50, 50, 0.9); border-radius: 50%;"></div>Major Hubs (>50 Routes)</div>
        <div class="metric"><div class="color-box" style="background: rgba(0, 255, 255, 0.6); border-radius: 50%;"></div>Regional Airports</div>

        <div style="margin-top: 15px; margin-bottom: 5px; font-size: 11px; color: #aaa; text-transform: uppercase;">Flight Distance (Color Scale)</div>
        <div class="legend-gradient"></div>
        <div class="legend-labels">
            <span>Short (< 2k km)</span>
            <span>Long (> 10k km)</span>
        </div>
    </div>
    <canvas id="globe"></canvas>

    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://unpkg.com/topojson@3"></script>

    <script>
        const canvas = document.getElementById("globe");
        const context = canvas.getContext("2d");

        function resize() {
            const width = window.innerWidth;
            const height = window.innerHeight;
            const dpr = window.devicePixelRatio || 1;
            canvas.width = width * dpr;
            canvas.height = height * dpr;
            canvas.style.width = width + "px";
            canvas.style.height = height + "px";
            context.scale(dpr, dpr);
            return { width, height };
        }
        let { width, height } = resize();

        const projection = d3.geoOrthographic()
            .scale(height / 1.9)
            .translate([width / 2, height / 2]);
        const path = d3.geoPath(projection, context);

        // 🌟 1. 定义颜色比例尺 (实现 PDF 中的 Section 4.1)
        // 使用 Turbo 或 Plasma 这种科学可视化常用的色谱
        // 0km -> 蓝色, 5000km -> 青色, 10000km -> 粉红/紫色
        const colorScale = d3.scaleSequential(d3.interpolateCool) 
            .domain([0, 12000]); // 假设最长航线大概 12000 公里

        Promise.all([
            d3.json("https://unpkg.com/world-atlas@1/world/110m.json"),
            d3.json("data.json")
        ]).then(([world, data]) => {
            const land = topojson.feature(world, world.objects.countries);
            const airportMap = new Map(data.airports.map(d => [d.code, d]));

            // 🌟 2. 预处理：计算度和距离
            const airportCounts = {};
            
            const routes = data.routes.map(r => {
                const src = airportMap.get(r.source);
                const tgt = airportMap.get(r.target);
                if (!src || !tgt) return null;

                // 统计度 (Degree)
                airportCounts[r.source] = (airportCounts[r.source] || 0) + 1;
                airportCounts[r.target] = (airportCounts[r.target] || 0) + 1;

                // 计算地理距离 (Distance)
                // d3.geoDistance 返回的是弧度，乘以地球半径 6371 得到公里
                const distance = d3.geoDistance(src.loc, tgt.loc) * 6371;

                return {
                    type: "LineString", 
                    coordinates: [src.loc, tgt.loc],
                    distance: distance // 把距离存进去，一会儿画图用
                };
            }).filter(d => d);

            // 绑定度数据回机场
            data.airports.forEach(d => d.degree = airportCounts[d.code] || 0);
            data.airports.sort((a, b) => a.degree - b.degree); // 小机场先画

            const rScale = d3.scaleSqrt().domain([0, d3.max(Object.values(airportCounts))]).range([1, 6]);

            d3.timer((elapsed) => {
                projection.rotate([elapsed * 0.005, -10]);
                context.clearRect(0, 0, width, height);

                // 画地球背景
                context.beginPath(); path({type: "Sphere"}); context.fillStyle = "#111"; context.fill();
                
                // 画陆地
                context.beginPath(); path(land); context.fillStyle = "#222"; context.fill(); 
                context.strokeStyle = "#000"; context.lineWidth = 0.5; context.stroke();

                // 🌟 3. 画航线：根据距离上色 (核心分析功能)
                routes.forEach(route => {
                    context.beginPath();
                    path(route);
                    // 这里的颜色是动态计算的！
                    context.strokeStyle = colorScale(route.distance);
                    // 距离越远，线条稍微粗一点点，透明度低一点
                    context.globalAlpha = 0.3; 
                    context.lineWidth = 0.6;
                    context.stroke();
                });
                context.globalAlpha = 1.0; // 恢复不透明

                // 画机场
                data.airports.forEach(d => {
                    const p = projection(d.loc);
                    // 简单的背面剔除
                    if (d3.geoDistance(d.loc, projection.invert([width/2, height/2])) > 1.57) return;

                    context.beginPath();
                    context.arc(p[0], p[1], rScale(d.degree), 0, 2 * Math.PI);
                    
                    if (d.degree > 50) {
                        context.fillStyle = "rgba(255, 50, 50, 0.9)";
                    } else {
                        context.fillStyle = "#fff";
                    }
                    context.fill();
                });
                
                // 加上光晕，增加美感
                context.beginPath(); path({type: "Sphere"});
                context.strokeStyle = "rgba(255,255,255,0.1)"; context.lineWidth = 1.5; context.stroke();
            });
        });

        window.addEventListener('resize', () => {
             const dim = resize();
             width = dim.width; height = dim.height;
             projection.translate([width / 2, height / 2]).scale(height / 1.9);
        });
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ Data Science 最终版已生成！包含距离分析和度中心性分析。")
