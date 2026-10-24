import { useState } from 'react'
import './App.css'

const NAME = 'Tornike'

function App() {
  const [tasks, setTasks] = useState([
    { id: 1, text: 'Create an S3 bucket', done: true },
    { id: 2, text: 'Build the React app', done: true },
    { id: 3, text: 'Host it with the boto3 CLI', done: false },
  ])
  const [text, setText] = useState('')

  const addTask = (event) => {
    event.preventDefault()
    if (!text.trim()) return
    setTasks([...tasks, { id: Date.now(), text: text.trim(), done: false }])
    setText('')
  }

  const toggleTask = (id) =>
    setTasks(tasks.map((task) => (task.id === id ? { ...task, done: !task.done } : task)))

  const removeTask = (id) => setTasks(tasks.filter((task) => task.id !== id))

  const doneCount = tasks.filter((task) => task.done).length

  return (
    <main>
      <header>
        <p className="eyebrow">React.js on Amazon S3</p>
        <h1>{NAME}</h1>
        <p className="subtitle">BTU · AWS boto3 course</p>
      </header>

      <section className="card">
        <h2>
          Tasks <span>{doneCount}/{tasks.length} done</span>
        </h2>

        <form onSubmit={addTask}>
          <input
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Add a task…"
            aria-label="New task"
          />
          <button type="submit">Add</button>
        </form>

        <ul>
          {tasks.map((task) => (
            <li key={task.id} className={task.done ? 'done' : ''}>
              <label>
                <input
                  type="checkbox"
                  checked={task.done}
                  onChange={() => toggleTask(task.id)}
                />
                {task.text}
              </label>
              <button className="remove" onClick={() => removeTask(task.id)} aria-label="Remove">
                ×
              </button>
            </li>
          ))}
        </ul>
      </section>

      <footer>Built with Vite + React, deployed with boto3</footer>
    </main>
  )
}

export default App
