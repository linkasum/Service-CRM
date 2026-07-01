import React, { useRef, useImperativeHandle, forwardRef, useEffect, useState } from 'react'
import hugerte from 'hugerte'
import 'hugerte/models/dom'
import 'hugerte/icons/default'
import 'hugerte/themes/silver'
import 'hugerte/skins/ui/oxide/skin.js'
import 'hugerte/skins/ui/oxide/content.js'
import 'hugerte/skins/content/default/content.js'

// Plugins
import 'hugerte/plugins/table'
import 'hugerte/plugins/advlist'
import 'hugerte/plugins/link'
import 'hugerte/plugins/lists'
import 'hugerte/plugins/image'
import 'hugerte/plugins/code'
import 'hugerte/plugins/searchreplace'
import 'hugerte/plugins/wordcount'
import 'hugerte/plugins/autolink'
import 'hugerte/plugins/charmap'
import 'hugerte/plugins/preview'
import 'hugerte/plugins/visualblocks'

interface HugerteEditorProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  readOnly?: boolean
  height?: string
}

export interface HugerteEditorRef {
  getEditor: () => any
}

const HugerteEditor = forwardRef<HugerteEditorRef, HugerteEditorProps>(({
  value,
  onChange,
  placeholder,
  readOnly = false,
  height = '500px'
}, ref) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const editorRef = useRef<any>(null)
  const [isReady, setIsReady] = useState(false)

  useImperativeHandle(ref, () => ({
    getEditor: () => editorRef.current
  }))

  useEffect(() => {
    if (!containerRef.current) return

    if (editorRef.current) {
      try {
        editorRef.current.destroy()
      } catch (e) {}
      editorRef.current = null
    }

    let editorInstance: any = null

    try {
      const editor = hugerte.init({
        target: containerRef.current,
        height: height,
        menubar: false,
        read_only: readOnly,
        placeholder: placeholder || 'Введите текст...',
        plugins: [
          'advlist', 'autolink', 'charmap', 'code', 'image', 'link', 'lists',
          'preview', 'searchreplace', 'table', 'visualblocks', 'wordcount'
        ].join(' '),
        toolbar: 'undo redo | formatselect | bold italic underline strikethrough | forecolor backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | table | link image | code | removeformat',
        skin_url: 'default',
        content_css: 'default',
        branding: false,
        content_style: `
          body { font-family: Arial, sans-serif; font-size: 14px; }
          table { border-collapse: collapse; width: 100%; }
          td, th { border: 1px solid #000; padding: 8px; }
          th { background: #e0e0e0; }
        `,
        setup: (ed: any) => {
          editorInstance = ed
          
          ed.on('init', () => {
            // Set content after editor is fully initialized
            if (value && value.length > 0) {
              try {
                ed.setContent(value)
              } catch (e) {
                console.error('Error setting initial content:', e)
              }
            }
            setIsReady(true)
          })

          ed.on('change', () => {
            try {
              onChange(ed.getContent())
            } catch (e) {}
          })
        }
      })

      editorRef.current = editor
      console.log('Hugerte initialized')
    } catch (error) {
      console.error('Hugerte init error:', error)
    }

    return () => {
      if (editorRef.current) {
        try {
          editorRef.current.destroy()
        } catch (e) {}
        editorRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    if (isReady && editorRef.current && typeof editorRef.current.getContent === 'function' && value !== undefined) {
      try {
        const currentContent = editorRef.current.getContent()
        if (currentContent !== value) {
          editorRef.current.setContent(value || '')
        }
      } catch (e) {
        console.error('Error setting content:', e)
      }
    }
  }, [value, isReady])

  return (
    <div>
      <div style={{ 
        display: 'flex', gap: 4, padding: '4px 8px', 
        background: '#f5f5f5', border: '1px solid #d9d9d9', 
        borderBottom: 'none', borderRadius: '4px 4px 0 0',
        alignItems: 'center', flexWrap: 'wrap'
      }}>
        <select 
          style={{ padding: '2px 4px', fontSize: 12, border: '1px solid #ccc', borderRadius: 3 }}
          onChange={(e) => {
            if (editorRef.current && e.target.value) {
              editorRef.current.execCommand('FontSize', false, e.target.value)
            }
          }}
          defaultValue=""
        >
          <option value="" disabled>Размер шрифта</option>
          <option value="8pt">8pt</option>
          <option value="9pt">9pt</option>
          <option value="10pt">10pt</option>
          <option value="11pt">11pt</option>
          <option value="12pt">12pt</option>
          <option value="14pt">14pt</option>
          <option value="16pt">16pt</option>
          <option value="18pt">18pt</option>
          <option value="20pt">20pt</option>
          <option value="24pt">24pt</option>
          <option value="28pt">28pt</option>
          <option value="36pt">36pt</option>
        </select>
        <select 
          style={{ padding: '2px 4px', fontSize: 12, border: '1px solid #ccc', borderRadius: 3 }}
          onChange={(e) => {
            if (editorRef.current && e.target.value) {
              editorRef.current.execCommand('FontName', false, e.target.value)
            }
          }}
          defaultValue=""
        >
          <option value="" disabled>Шрифт</option>
          <option value="Arial">Arial</option>
          <option value="Times New Roman">Times New Roman</option>
          <option value="Courier New">Courier New</option>
          <option value="Georgia">Georgia</option>
          <option value="Verdana">Verdana</option>
          <option value="Tahoma">Tahoma</option>
          <option value="Impact">Impact</option>
        </select>
      </div>
      <div 
        ref={containerRef}
        style={{ 
          border: '1px solid #d9d9d9', 
          borderTop: 'none',
          borderRadius: '0 0 4px 4px',
          minHeight: height
        }} 
      />
    </div>
  )
})

HugerteEditor.displayName = 'HugerteEditor'

export default HugerteEditor
