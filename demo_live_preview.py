#!/usr/bin/env python3
"""
Demo script for NEXUS Live Preview System
Shows how to use the preview system with different frameworks
"""

import os
import asyncio
from pathlib import Path
import json


def create_react_demo():
    """Create a React demo project"""
    demo_dir = Path("demo_react_preview")
    demo_dir.mkdir(exist_ok=True)
    
    # Create package.json
    package_json = {
        "name": "react-preview-demo",
        "version": "1.0.0",
        "dependencies": {
            "react": "^18.0.0",
            "react-dom": "^18.0.0"
        }
    }
    
    with open(demo_dir / "package.json", "w") as f:
        json.dump(package_json, f, indent=2)
    
    # Create index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>React Preview Demo</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .counter {
            text-align: center;
            padding: 20px;
        }
        .counter button {
            margin: 0 10px;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            border-radius: 4px;
            background: #007bff;
            color: white;
            cursor: pointer;
        }
        .counter button:hover {
            background: #0056b3;
        }
        .count-display {
            font-size: 48px;
            margin: 20px 0;
            color: #333;
        }
    </style>
</head>
<body>
    <div id="root"></div>
    
    <script type="text/babel">
        const { useState, useEffect } = React;
        
        function Counter() {
            const [count, setCount] = useState(0);
            
            useEffect(() => {
                // Report state to preview system
                if (window.__NEXUS_PREVIEW__) {
                    window.__NEXUS_PREVIEW__.captureState('counter', { count });
                }
            }, [count]);
            
            return (
                <div className="counter">
                    <h1>React Counter Demo</h1>
                    <div className="count-display">{count}</div>
                    <button onClick={() => setCount(count - 1)}>Decrease</button>
                    <button onClick={() => setCount(0)}>Reset</button>
                    <button onClick={() => setCount(count + 1)}>Increase</button>
                </div>
            );
        }
        
        function App() {
            return (
                <div className="container">
                    <Counter />
                    <p style={{textAlign: 'center', marginTop: '20px', color: '#666'}}>
                        Edit this file and see changes instantly with hot reload!
                    </p>
                </div>
            );
        }
        
        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>"""
    
    with open(demo_dir / "index.html", "w") as f:
        f.write(index_html)
    
    print(f"✅ React demo created in {demo_dir}")
    return demo_dir


def create_vue_demo():
    """Create a Vue.js demo project"""
    demo_dir = Path("demo_vue_preview")
    demo_dir.mkdir(exist_ok=True)
    
    # Create package.json
    package_json = {
        "name": "vue-preview-demo",
        "version": "1.0.0",
        "dependencies": {
            "vue": "^3.0.0"
        }
    }
    
    with open(demo_dir / "package.json", "w") as f:
        json.dump(package_json, f, indent=2)
    
    # Create index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vue Preview Demo</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        #app {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .todo-list {
            margin-top: 20px;
        }
        .todo-item {
            padding: 10px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .todo-item.completed {
            text-decoration: line-through;
            opacity: 0.6;
        }
        input[type="text"] {
            width: 70%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            background: #42b883;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background: #33a06f;
        }
        .delete-btn {
            background: #dc3545;
            padding: 5px 10px;
            font-size: 12px;
        }
        .delete-btn:hover {
            background: #c82333;
        }
    </style>
</head>
<body>
    <div id="app">
        <h1>{{ title }}</h1>
        <div style="margin-bottom: 20px;">
            <input 
                v-model="newTodo" 
                @keyup.enter="addTodo"
                placeholder="Add a new todo..."
                type="text"
            >
            <button @click="addTodo">Add Todo</button>
        </div>
        
        <div class="todo-list">
            <div 
                v-for="(todo, index) in todos" 
                :key="todo.id"
                :class="['todo-item', { completed: todo.completed }]"
            >
                <span @click="toggleTodo(index)" style="cursor: pointer;">
                    {{ todo.text }}
                </span>
                <button class="delete-btn" @click="deleteTodo(index)">Delete</button>
            </div>
        </div>
        
        <p v-if="todos.length === 0" style="text-align: center; color: #999;">
            No todos yet. Add one above!
        </p>
    </div>
    
    <script>
        const { createApp } = Vue;
        
        const app = createApp({
            data() {
                return {
                    title: 'Vue Todo App',
                    newTodo: '',
                    todos: [
                        { id: 1, text: 'Learn Vue 3', completed: false },
                        { id: 2, text: 'Build something awesome', completed: false }
                    ]
                }
            },
            methods: {
                addTodo() {
                    if (this.newTodo.trim()) {
                        this.todos.push({
                            id: Date.now(),
                            text: this.newTodo,
                            completed: false
                        });
                        this.newTodo = '';
                        
                        // Report state to preview system
                        if (window.__NEXUS_PREVIEW__) {
                            window.__NEXUS_PREVIEW__.captureState('todo-app', { 
                                todos: this.todos 
                            });
                        }
                    }
                },
                toggleTodo(index) {
                    this.todos[index].completed = !this.todos[index].completed;
                },
                deleteTodo(index) {
                    this.todos.splice(index, 1);
                }
            },
            mounted() {
                window.vueApp = this;
            }
        });
        
        app.mount('#app');
    </script>
</body>
</html>"""
    
    with open(demo_dir / "index.html", "w") as f:
        f.write(index_html)
    
    print(f"✅ Vue demo created in {demo_dir}")
    return demo_dir


def create_vanilla_demo():
    """Create a vanilla JavaScript demo project"""
    demo_dir = Path("demo_vanilla_preview")
    demo_dir.mkdir(exist_ok=True)
    
    # Create index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vanilla JS Preview Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .color-picker {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }
        .color-btn {
            width: 50px;
            height: 50px;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .color-btn:hover {
            transform: scale(1.1);
        }
        .canvas {
            width: 100%;
            height: 300px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin: 20px 0;
            position: relative;
            overflow: hidden;
        }
        .shape {
            position: absolute;
            transition: all 0.3s;
        }
        .controls {
            display: flex;
            gap: 10px;
            justify-content: center;
        }
        .controls button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background: #4CAF50;
            color: white;
            cursor: pointer;
        }
        .controls button:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Interactive Canvas Demo</h1>
        
        <div class="color-picker">
            <button class="color-btn" style="background: #ff6b6b" data-color="#ff6b6b"></button>
            <button class="color-btn" style="background: #4ecdc4" data-color="#4ecdc4"></button>
            <button class="color-btn" style="background: #45b7d1" data-color="#45b7d1"></button>
            <button class="color-btn" style="background: #f9ca24" data-color="#f9ca24"></button>
            <button class="color-btn" style="background: #6c5ce7" data-color="#6c5ce7"></button>
        </div>
        
        <div id="canvas" class="canvas"></div>
        
        <div class="controls">
            <button onclick="addCircle()">Add Circle</button>
            <button onclick="addSquare()">Add Square</button>
            <button onclick="clearCanvas()">Clear</button>
        </div>
        
        <p style="text-align: center; color: #666; margin-top: 20px;">
            Click shapes to move them. Select a color before adding shapes.
        </p>
    </div>
    
    <script>
        let selectedColor = '#ff6b6b';
        let shapeCount = 0;
        
        // Color picker
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                selectedColor = this.dataset.color;
                document.querySelectorAll('.color-btn').forEach(b => {
                    b.style.border = 'none';
                });
                this.style.border = '3px solid #333';
            });
        });
        
        // Add circle
        function addCircle() {
            const canvas = document.getElementById('canvas');
            const circle = document.createElement('div');
            circle.className = 'shape';
            circle.id = 'shape-' + shapeCount++;
            circle.style.width = '60px';
            circle.style.height = '60px';
            circle.style.borderRadius = '50%';
            circle.style.background = selectedColor;
            circle.style.left = Math.random() * (canvas.offsetWidth - 60) + 'px';
            circle.style.top = Math.random() * (canvas.offsetHeight - 60) + 'px';
            circle.style.cursor = 'move';
            
            makeMoveable(circle);
            canvas.appendChild(circle);
            
            reportInteraction('shape_added', { type: 'circle', color: selectedColor });
        }
        
        // Add square
        function addSquare() {
            const canvas = document.getElementById('canvas');
            const square = document.createElement('div');
            square.className = 'shape';
            square.id = 'shape-' + shapeCount++;
            square.style.width = '60px';
            square.style.height = '60px';
            square.style.borderRadius = '8px';
            square.style.background = selectedColor;
            square.style.left = Math.random() * (canvas.offsetWidth - 60) + 'px';
            square.style.top = Math.random() * (canvas.offsetHeight - 60) + 'px';
            square.style.cursor = 'move';
            
            makeMoveable(square);
            canvas.appendChild(square);
            
            reportInteraction('shape_added', { type: 'square', color: selectedColor });
        }
        
        // Make shapes moveable
        function makeMoveable(element) {
            let isDragging = false;
            let currentX;
            let currentY;
            let initialX;
            let initialY;
            let xOffset = 0;
            let yOffset = 0;
            
            element.addEventListener('mousedown', dragStart);
            element.addEventListener('mouseup', dragEnd);
            element.addEventListener('mousemove', drag);
            
            function dragStart(e) {
                initialX = e.clientX - xOffset;
                initialY = e.clientY - yOffset;
                
                if (e.target === element) {
                    isDragging = true;
                }
            }
            
            function dragEnd(e) {
                initialX = currentX;
                initialY = currentY;
                isDragging = false;
            }
            
            function drag(e) {
                if (isDragging) {
                    e.preventDefault();
                    currentX = e.clientX - initialX;
                    currentY = e.clientY - initialY;
                    xOffset = currentX;
                    yOffset = currentY;
                    
                    element.style.transform = `translate(${currentX}px, ${currentY}px)`;
                }
            }
        }
        
        // Clear canvas
        function clearCanvas() {
            document.getElementById('canvas').innerHTML = '';
            shapeCount = 0;
            reportInteraction('canvas_cleared', {});
        }
        
        // Report interactions to preview system
        function reportInteraction(action, data) {
            if (window.__NEXUS_PREVIEW__) {
                window.__NEXUS_PREVIEW__.captureState('canvas', {
                    action: action,
                    shapeCount: shapeCount,
                    data: data
                });
            }
        }
        
        // Initialize first color selection
        document.querySelector('.color-btn').click();
    </script>
</body>
</html>"""
    
    with open(demo_dir / "index.html", "w") as f:
        f.write(index_html)
    
    # Create additional CSS file for hot reload testing
    css_file = """/* Additional styles for hot reload testing */
.shape {
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.shape:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

/* You can edit this file to see hot reload in action */"""
    
    with open(demo_dir / "styles.css", "w") as f:
        f.write(css_file)
    
    print(f"✅ Vanilla JS demo created in {demo_dir}")
    return demo_dir


def create_static_demo():
    """Create a static HTML demo"""
    demo_dir = Path("demo_static_preview")
    demo_dir.mkdir(exist_ok=True)
    
    # Create index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Static Site Preview Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        header {
            background: #2c3e50;
            color: white;
            padding: 1rem 0;
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
        }
        nav {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        nav ul {
            list-style: none;
            display: flex;
            gap: 30px;
        }
        nav a {
            color: white;
            text-decoration: none;
            transition: opacity 0.3s;
        }
        nav a:hover {
            opacity: 0.8;
        }
        main {
            margin-top: 60px;
        }
        .hero {
            background: linear-gradient(135deg, #3498db, #2c3e50);
            color: white;
            padding: 100px 20px;
            text-align: center;
        }
        .hero h1 {
            font-size: 3rem;
            margin-bottom: 20px;
        }
        .hero p {
            font-size: 1.2rem;
            max-width: 600px;
            margin: 0 auto;
        }
        .features {
            padding: 80px 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .features h2 {
            text-align: center;
            margin-bottom: 50px;
            font-size: 2.5rem;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }
        .feature {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
        }
        .feature h3 {
            margin-bottom: 15px;
            color: #2c3e50;
        }
        footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 30px 20px;
        }
    </style>
</head>
<body>
    <header>
        <nav>
            <div class="logo">
                <h2>Static Demo</h2>
            </div>
            <ul>
                <li><a href="#home">Home</a></li>
                <li><a href="#features">Features</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section class="hero" id="home">
            <h1>Welcome to Static Site Preview</h1>
            <p>Experience real-time preview with hot reload for your static websites. Edit this file and watch it update instantly!</p>
        </section>
        
        <section class="features" id="features">
            <h2>Features</h2>
            <div class="feature-grid">
                <div class="feature">
                    <h3>🔥 Hot Reload</h3>
                    <p>See changes instantly as you edit your HTML, CSS, and JavaScript files.</p>
                </div>
                <div class="feature">
                    <h3>📱 Responsive Preview</h3>
                    <p>Test your site on different screen sizes and devices.</p>
                </div>
                <div class="feature">
                    <h3>🎨 Terminal Preview</h3>
                    <p>View your site structure in the terminal with ASCII art rendering.</p>
                </div>
                <div class="feature">
                    <h3>📊 Performance Metrics</h3>
                    <p>Monitor load times, memory usage, and other performance indicators.</p>
                </div>
            </div>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2024 NEXUS Live Preview. Built with ❤️ for developers.</p>
    </footer>
</body>
</html>"""
    
    with open(demo_dir / "index.html", "w") as f:
        f.write(index_html)
    
    print(f"✅ Static site demo created in {demo_dir}")
    return demo_dir


async def run_preview_demo():
    """Run preview demos"""
    print("🚀 NEXUS Live Preview Demo")
    print("=" * 50)
    print("\nSelect a demo to run:")
    print("1. React Counter App")
    print("2. Vue Todo App")
    print("3. Vanilla JS Interactive Canvas")
    print("4. Static Website")
    print("5. Create all demos (don't run preview)")
    
    choice = input("\nEnter your choice (1-5): ")
    
    if choice == "5":
        create_react_demo()
        create_vue_demo()
        create_vanilla_demo()
        create_static_demo()
        print("\n✅ All demos created!")
        print("\nTo run a demo, use:")
        print("python nexus_live_preview.py --root demo_[framework]_preview")
        return
    
    # Create selected demo
    demo_dirs = {
        "1": create_react_demo(),
        "2": create_vue_demo(),
        "3": create_vanilla_demo(),
        "4": create_static_demo()
    }
    
    if choice not in demo_dirs:
        print("Invalid choice!")
        return
    
    demo_dir = demo_dirs[choice]
    
    print(f"\n🎯 Starting preview server for {demo_dir}...")
    print("\nPreview will be available at:")
    print("- Web: http://localhost:3000")
    print("- Terminal: Check your console")
    print("\nPress Ctrl+C to stop\n")
    
    # Run the preview server
    cmd = f"{sys.executable} nexus_live_preview.py --root {demo_dir}"
    subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    asyncio.run(run_preview_demo())