import React, { useEffect, useRef, useImperativeHandle, forwardRef } from 'react'
import { Editor } from 'hugerte'
import 'hugerte/skins/ui/oxide/skin.min.css'

interface HugeRTEProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  readOnly?: boolean
}

export interface HugeRTEText {
  getEditor: () => any
}

const HugeRTE = forwardRef<HugeRTEText, HugeRTEProps>(({ value, onChange, placeholder, readOnly }, ref) => {
  const editorRef = useRef<any>(null)

  useImperativeHandle(ref, () => ({
    getEditor: () => editorRef.current?.editor
  }))

  const handleInit = (editor: any) => {
    editorRef.current = editor
  }

  const handleEditorChange = (content: string, editor: any) => {
    onChange(content)
  }

  // Custom toolbar configuration
  const toolbar = [
    { name: 'document', items: ['source'] },
    { name: 'clipboard', items: ['cut', 'copy', 'paste', 'undo', 'redo'] },
    { name: 'editing', items: ['find', 'replace', 'selectAll'] },
    { name: 'basic', items: ['bold', 'italic', 'underline', 'strike', 'cleanup'] },
    { name: 'paragraph', items: ['bullist', 'numlist', 'outdent', 'indent', 'blockquote'] },
    { name: 'links', items: ['link', 'unlink'] },
    { name: 'insert', items: ['table', 'charmap', 'image'] },
    { name: 'styles', items: ['styles', 'formats', 'alignleft', 'aligncenter', 'alignright', 'alignjustify'] },
  ]

  return (
    <Editor
      initialValue={value}
      onEditorChange={handleEditorChange}
      onInit={handleInit}
      init={{
        placeholder: placeholder || 'Введите текст...',
        readOnly: readOnly || false,
        height: '100%',
        min_height: '400px',
        menubar: false,
        skin: 'oxide',
        plugins: [
          'advlist', 'autolink', 'charmap', 'code', 'codesample',
          'help', 'image', 'link', 'lists', 'media', 'preview',
          'searchreplace', 'table', 'visualblocks', 'wordcount',
        ],
        toolbar: toolbar,
        branding: false,
        content_style: `
          body { font-family: Arial, sans-serif; font-size: 14px; }
          table { border-collapse: collapse; width: 100%; }
          td, th { border: 1px solid #000; padding: 8px; }
          th { background: #e0e0e0; }
        `,
      }}
    />
  )
})

HugeRTE.displayName = 'HugeRTE'

export default HugeRTE
