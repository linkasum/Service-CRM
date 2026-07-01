import React, { useRef, useImperativeHandle, forwardRef } from 'react'
import { Editor } from '@tinymce/tinymce-react'

interface TinyMCEditorProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  readOnly?: boolean
  height?: string
}

export interface TinyMCEditorRef {
  getEditor: () => any
}

const TinyMCEditor = forwardRef<TinyMCEditorRef, TinyMCEditorProps>(({ 
  value, 
  onChange, 
  placeholder, 
  readOnly = false,
  height = '400px'
}, ref) => {
  const editorRef = useRef<any>(null)

  useImperativeHandle(ref, () => ({
    getEditor: () => editorRef.current
  }))

  const handleEditorChange = (content: string, editor: any) => {
    onChange(content)
  }

  return (
    <Editor
      apiKey="no-api-key"  // Using free tier without API key
      initialValue={value}
      onEditorChange={handleEditorChange}
      onInit={(evt, editor) => {
        editorRef.current = editor
      }}
      init={{
        placeholder: placeholder || 'Введите текст...',
        readonly: readOnly,
        height: height,
        menubar: false,
        plugins: [
          'advlist', 'autolink', 'charmap', 'code', 'codesample',
          'help', 'image', 'link', 'lists', 'media', 'preview',
          'searchreplace', 'table', 'visualblocks', 'wordcount',
        ],
        toolbar: 'undo redo | formatselect | bold italic underline strikethrough | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | table | link image | removeformat',
        branding: false,
        content_style: `
          body { font-family: Arial, sans-serif; font-size: 14px; }
          table { border-collapse: collapse; width: 100%; }
          td, th { border: 1px solid #000; padding: 8px; }
          th { background: #e0e0e0; }
        `,
        table_default_attributes: {
          border: 1
        },
        table_advtab_attributes: true,
        table_default_styles: {
          'border-collapse': 'collapse',
          'width': '100%'
        },
      }}
    />
  )
})

TinyMCEditor.displayName = 'TinyMCEditor'

export default TinyMCEditor
