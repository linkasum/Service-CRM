import React, { forwardRef, useImperativeHandle } from 'react'
import ReactQuill from 'react-quill-new'
import 'react-quill-new/dist/quill.snow.css'

// Import table module
import 'quill-better-table'

interface QuillEditorProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  readOnly?: boolean
  height?: string
}

export interface QuillEditorRef {
  getEditor: () => any
}

const QuillEditor = forwardRef<QuillEditorRef, QuillEditorProps>(({ 
  value, 
  onChange, 
  placeholder,
  readOnly = false,
  height = '400px'
}, ref) => {
  
  useImperativeHandle(ref, () => ({
    getEditor: () => null
  }))

  const modules = {
    toolbar: {
      container: [
        [{ header: [1, 2, 3, 4, 5, 6, false] }],
        ['bold', 'italic', 'underline', 'strike'],
        [{ color: [] }, { background: [] }],
        [{ align: [] }],
        [{ list: 'ordered' }, { list: 'bullet' }],
        [{ indent: '-1' }, { indent: '+1' }],
        ['link', 'image'],
        ['clean'],
        ['code-block'],
        ['table'],  // Table support
      ],
      handlers: {
        table: function() {}  // Will use default handler
      }
    },
    table: false,  // Disable default table module, use quill-better-table
    'better-table': {
      operationMenu: {
        items: {
          insertRow: { icon: 'plus', title: 'Insert Row' },
          removeRow: { icon: 'minus', title: 'Remove Row' },
          insertColumn: { icon: 'plus', title: 'Insert Column' },
          removeColumn: { icon: 'minus', title: 'Remove Column' }
        }
      }
    },
    keyboard: {
      bindings: {
        'better-table': {
          key: 'tab',
          handler: function() {
            return true
          }
        }
      }
    }
  }

  const formats = [
    'header', 'bold', 'italic', 'underline', 'strike',
    'color', 'background', 'align', 'list', 'bullet', 'indent',
    'link', 'image', 'code-block', 'table'
  ]

  return (
    <ReactQuill
      theme="snow"
      value={value}
      onChange={onChange}
      modules={modules}
      formats={formats}
      style={{ background: '#fff', height: height }}
      placeholder={placeholder || 'Введите текст...'}
      readOnly={readOnly}
    />
  )
})

QuillEditor.displayName = 'QuillEditor'

export default QuillEditor
