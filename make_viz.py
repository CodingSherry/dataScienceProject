import os

print("正在生成最终进化版可视化代码 (带标签+科技配色)...")

html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Global Flight Analysis - Pro</title>
    <style>
        /* 背景改为深空蓝，更具科技感 */
        body { background: radial-gradient(circle at center, #0b1a2a 0%, #000000 100%); margin: 0; overflow: hidden; font-family: 'Roboto Mono', 'Helvetica Neue', monospace; }
        canvas { display: block; cursor: grab; }
        canvas:active { cursor: grabbing; }
        
        #ui-layer { 
            position: absolute; top: 30px; left: 30px; pointer-events: none;
            background: rgba(10, 20, 30, 0.85); padding: 20px; border-radius: 4px;
            border: 1px solid rgba(0, 242, 254, 0.3); backdrop-filter: blur(10px);
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.1);
            width: 240px;
            color: #fff;
        }
        
        h1 { margin: 0 0 15px 0; font-size: 16px; color: #00f2fe; text-transform: uppercase; letter-spacing: 2px; border-bottom: 1px solid rgba(0, 242, 254, 0.3); padding-bottom: 10px; text-shadow: 0 0 5px rgba(0, 242, 254, 0.5); }
        
        .metric { display: flex; align-items: center; margin-bottom: 8px; font-size: 11px; color: #aaccff; }
        .color-box { width: 8px; height: 8px; margin-right: 10px; }
        
        /* 按钮样式升级 */
        .controls { margin-top: 20px; pointer-events: auto; }
        button {
            background: rgba(0, 242, 254, 0.1); border: 1px solid rgba(0, 242, 254, 0.4);
            color: #00f2fe; padding: 10px 12px; cursor: pointer;
            font-size: 11px; width: 100%; margin-bottom: 8px; transition: all 0.2s;
            text-transform: uppercase; letter-spacing: 1px; font-family: inherit;
        }
        button:hover { background: rgba(0, 242, 254, 0.3); box-shadow: 0 0 10px rgba(0, 242, 254, 0.4); }
        button.active { background: #00f2fe; color: #000; font-weight: bold; box-shadow: 0 0 15px rgba(0, 242, 254, 0.6); }

        .legend-gradient {
            width: 100%; height: 4px; margin: 8px 0;
            background: linear-gradient(to right, #00f2fe, #4facfe, #f093fb, #ff0055);
            border-radius: 2px;
        }
        .legend-labels { display: flex; justify-content: space-between; font-size: 9px; color: #557799; }
    </style>
</head>
<body>
    <div id="ui-layer">
        <h1>Global Network</h1>
        
        <div style="font-size: 9px; color: #557799; margin-bottom:5px;">HUB STATUS</div>
        <div class="metric"><div class="color-box" style="background: #ff3366; border-radius: 50%; box-shadow: 0 0 5px #ff3366;"></div>Super Hub (>100 Routes)</div>
        <div class="metric"><div class="color-box" style="background: rgba(255, 255, 255, 0.6); border-radius: 50%;"></div>Connecting Airport</div>

        <div style="font-size: 9px; color: #557799; margin-top: 15px; margin-bottom:5px;">FLIGHT RANGE</div>
        <div class="legend-gradient"></div>
        <div class="legend-labels"><span>Regional</span><span>Intercontinental</span></div>

        <div class="controls">
            <button id="btn-filter" onclick="toggleFilter()">View: All Routes</button>
            <button id="btn-spin" onclick="toggleSpin()">Auto-Rotation: ON</button>
            <button id="btn-labels" onclick="toggleLabels()">Labels: ON</button>
        </div>
    </div>
    <canvas id="globe"></canvas>

    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://unpkg.com/topojson@3"></script>

    <script>
        const canvas = document.getElementById("globe");
        const context = canvas.getContext("2d");

        let config = { 
            isRotating: true, 
            showHubsOnly: false, 
            showLabels: true, // 新增：控制标签显示
            rotationAngle: 0 
        };

        // --- 交互功能 ---
        function toggleFilter() {
            config.showHubsOnly = !config.showHubsOnly;
            const btn = document.getElementById('btn-filter');
            if (config.showHubsOnly) {
                btn.innerText = "View: Super Hubs";
                btn.classList.add("active");
            } else {
                btn.innerText = "View: All Routes";
                btn.classList.remove("active");
            }
            render();
        }

        function toggleSpin() {
            config.isRotating = !config.isRotating;
            const btn = document.getElementById('btn-spin');
            btn.innerText = config.isRotating ? "Auto-Rotation: ON" : "Auto-Rotation: PAUSED";
            btn.style.opacity = config.isRotating ? "1" : "0.6";
        }
        
        function toggleLabels() {
            config.showLabels = !config.showLabels;
            const btn = document.getElementById('btn-labels');
            btn.innerText = config.showLabels ? "Labels: ON" : "Labels: OFF";
            btn.style.opacity = config.showLabels ? "1" : "0.6";
            render();
        }

        let drag = d3.drag().on("drag", (event) => {
            config.isRotating = false;
            document.getElementById('btn-spin').innerText = "Auto-Rotation: PAUSED";
            const rotate = projection.rotate();
            projection.rotate([rotate[0] + event.dx * 0.5, rotate[1] - event.dy * 0.5]);
            render();
        });
        d3.select(canvas).call(drag);

        function resize() {
            const width = window.innerWidth;
            const height = window.innerHeight;
            const dpr = window.devicePixelRatio || 1;
            canvas.width = width * dpr; canvas.height = height * dpr;
            canvas.style.width = width + "px"; canvas.style.height = height + "px";
            context.scale(dpr, dpr);
            return { width, height };
        }
        let { width, height } = resize();

        const projection = d3.geoOrthographic().scale(height / 2.0).translate([width / 2, height / 2]);
        const path = d3.geoPath(projection, context);
        // 配色升级：从青色(Short)到洋红(Long)
        const colorScale = d3.scaleSequential(d3.interpolateCool).domain([0, 13000]);
        
        let worldData, flightData, airportMap;

        function render() {
            if (!worldData || !flightData) return;
            context.clearRect(0, 0, width, height);

            // 1. [升级] 画海洋 (深蓝渐变)
            let grad = context.createRadialGradient(width/2, height/2, height/5, width/2, height/2, height/1.8);
            grad.addColorStop(0, "#081119");
            grad.addColorStop(1, "#000508");
            
            context.beginPath(); path({type: "Sphere"}); 
            context.fillStyle = grad; context.fill();

            // 2. [升级] 画陆地 (科技蓝灰 + 发光边缘)
            context.beginPath(); path(worldData); 
            context.fillStyle = "#1a2b3c"; context.fill(); // 陆地填充色
            context.strokeStyle = "rgba(0, 242, 254, 0.3)"; context.lineWidth = 0.8; context.stroke(); // 边缘发光色

            // 3. 画航线
            flightData.routes.forEach(route => {
                if (config.showHubsOnly) {
                    const src = airportMap.get(route.srcCode);
                    const tgt = airportMap.get(route.tgtCode);
                    if (!src || !tgt || src.degree <= 50 || tgt.degree <= 50) return; 
                }
                context.beginPath(); path(route);
                context.strokeStyle = colorScale(route.distance);
                context.lineWidth = config.showHubsOnly ? 1.2 : 0.5;
                context.globalAlpha = config.showHubsOnly ? 0.9 : 0.35; 
                context.stroke();
            });
            context.globalAlpha = 1.0;

            // 4. 画机场 & [升级] 标签
            flightData.airports.forEach(d => {
                // 背面剔除
                if (d3.geoDistance(d.loc, projection.invert([width/2, height/2])) > 1.57) return;
                if (config.showHubsOnly && d.degree <= 50) return;

                const p = projection(d.loc);
                const isSuperHub = d.degree > 100; // 定义超级枢纽阈值

                // 画点
                context.beginPath(); 
                let r = isSuperHub ? 4 : (config.showHubsOnly ? 2 : 1.2);
                context.arc(p[0], p[1], r, 0, 2 * Math.PI);
                
                if (d.degree > 50) {
                    context.fillStyle = "#ff3366"; // 醒目的玫红色
                    context.shadowBlur = 10; context.shadowColor = "#ff3366";
                } else {
                    context.fillStyle = "rgba(255, 255, 255, 0.7)";
                    context.shadowBlur = 0;
                }
                context.fill(); context.shadowBlur = 0;

                // [升级] 画文字标签 (只有当开启标签，且是超级枢纽时才显示)
                if (config.showLabels && isSuperHub) {
                    context.fillStyle = "#fff";
                    context.font = "bold 11px 'Roboto Mono', monospace";
                    context.textAlign = "left";
                    context.shadowBlur = 4; context.shadowColor = "#000"; // 文字描边效果
                    // 稍微偏移一点，别盖住点
                    context.fillText(d.code, p[0] + 8, p[1] + 4);
                    context.shadowBlur = 0;
                }
            });

            // 5. [升级] 大气层光晕 (Atmosphere Glow)
            context.beginPath(); path({type: "Sphere"});
            let atmosphere = context.createRadialGradient(width/2, height/2, height/2.1, width/2, height/2, height/1.95);
            atmosphere.addColorStop(0, "rgba(0, 242, 254, 0)");
            atmosphere.addColorStop(1, "rgba(0, 242, 254, 0.4)");
            context.fillStyle = atmosphere; context.fill();
        }

        Promise.all([
            d3.json("https://unpkg.com/world-atlas@1/world/110m.json"),
            d3.json("data.json")
        ]).then(([world, data]) => {
            worldData = topojson.feature(world, world.objects.countries);
            airportMap = new Map(data.airports.map(d => [d.code, d]));
            const airportCounts = {};

            const processedRoutes = data.routes.map(r => {
                const src = airportMap.get(r.source);
                const tgt = airportMap.get(r.target);
                if (!src || !tgt) return null;
                airportCounts[r.source] = (airportCounts[r.source] || 0) + 1;
                airportCounts[r.target] = (airportCounts[r.target] || 0) + 1;
                return {
                    type: "LineString", coordinates: [src.loc, tgt.loc],
                    distance: d3.geoDistance(src.loc, tgt.loc) * 6371,
                    srcCode: r.source, tgtCode: r.target
                };
            }).filter(d => d);

            data.airports.forEach(d => d.degree = airportCounts[d.code] || 0);
            data.airports.sort((a, b) => a.degree - b.degree);
            flightData = { airports: data.airports, routes: processedRoutes };

            d3.timer((elapsed) => {
                if (config.isRotating) {
                    config.rotationAngle += 0.2;
                    projection.rotate([config.rotationAngle, -10]);
                    render();
                }
            });
            render();
        });

        window.addEventListener('resize', () => {
             const dim = resize(); width = dim.width; height = dim.height;
             projection.translate([width / 2, height / 2]).scale(height / 2.0);
             render();
        });
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ PRO版可视化生成完毕！包含标签、光晕和科技配色。")
