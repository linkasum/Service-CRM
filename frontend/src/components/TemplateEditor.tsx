import React from 'react'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { Button, Space, message, Tag } from 'antd'
import { SaveOutlined, UndoOutlined, CodeOutlined, EyeOutlined, PlusOutlined } from '@ant-design/icons'

const VARIABLES = [
  { group: 'Заказ', vars: ['{order_id}', '{status}', '{created_at}', '{ready_at}', '{issued_at}'] },
  { group: 'Клиент', vars: ['{client_name}', '{client_phone}', '{client_email}', '{client_address}'] },
  { group: 'Устройство', vars: ['{device_category}', '{device_brand}', '{device_model}', '{serial_number}', '{accessories}'] },
  { group: 'Финансы', vars: ['{total_cost}', '{parts_cost}', '{work_cost}', '{paid_amount}'] },
  { group: 'Персонал', vars: ['{acceptor_username}', '{master_username}', '{company_name}', '{company_address}', '{company_phone}'] },
  { group: 'Прочее', vars: ['{complaint}', '{diagnostic_act_text}', '{warranty_days}', '{warranty_until}'] },
]

const formats = [
  'header', 'bold', 'italic', 'underline', 'strike',
  'color', 'background',
  'list', 'bullet', 'indent',
  'align', 'link', 'image',
  'table', 'blockquote', 'code-block',
  'size', 'font',
]

const modules = {
  toolbar: [
    [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
    [{ 'size': ['small', false, 'large', 'huge'] }],
    [{ 'font': [] }],
    ['bold', 'italic', 'underline', 'strike'],
    [{ 'color': [] }, { 'background': [] }],
    [{ 'list': 'ordered' }, { 'list': 'bullet' }, { 'indent': '-1' }, { 'indent': '+1' }],
    [{ 'align': [] }],
    ['link', 'image', 'table'],
    ['blockquote', 'code-block'],
    ['clean'],
  ],
}

interface TemplateEditorProps {
  value: string
  onChange: (value: string) => void
  onSave: () => void
  onSaveAndPreview: () => void
  height?: number
}

const TemplateEditor: React.FC<TemplateEditorProps> = ({
  value,
  onChange,
  onSave,
  onSaveAndPreview,
  height = 400,
}) => {
  const [showVariables, setShowVariables] = React.useState(false)

  const insertVariable = (variable: string) => {
    const quill = (document.querySelector('.ql-editor') as any)?.__quill
    if (quill) {
      const range = quill.getSelection(true)
      quill.insertText(range?.index || 0, variable)
      quill.setSelection((range?.index || 0) + variable.length)
    } else {
      // Fallback: вставляем в конец
      onChange(value + variable)
    }
  }

  return (
    <div>
      {/* Панель инструментов */}
      <Space wrap style={{ marginBottom: 8 }}>
        <Button size="small" icon={<PlusOutlined />} onClick={() => setShowVariables(!showVariables)}>
          Переменные
        </Button>
        <Button size="small" icon={<CodeOutlined />} onClick={() => {
          const html = value
          const textarea = document.createElement('textarea')
          textarea.value = html
          document.body.appendChild(textarea)
          textarea.select()
          document.execCommand('copy')
          document.body.removeChild(textarea)
          message.success('HTML скопирован')
        }}>
          Копировать HTML
        </Button>
        <Button size="small" icon={<EyeOutlined />} onClick={onSaveAndPreview}>
          Предпросмотр PDF
        </Button>
        <Button type="primary" size="small" icon={<SaveOutlined />} onClick={onSave}>
          Сохранить
        </Button>
      </Space>

      {/* Панель переменных */}
      {showVariables && (
        <div style={{
          marginBottom: 8,
          padding: 12,
          background: '#fafafa',
          borderRadius: 6,
          border: '1px solid #e8e8e8',
          maxHeight: 200,
          overflowY: 'auto',
        }}>
          <div style={{ marginBottom: 8, fontWeight: 600, fontSize: 12 }}>Вставляемые переменные (кликните чтобы вставить):</div>
          {VARIABLES.map(group => (
            <div key={group.group} style={{ marginBottom: 8 }}>
              <Tag color="blue" style={{ marginBottom: 4, fontSize: 11 }}>{group.group}</Tag>
              <Space wrap>
                {group.vars.map(v => (
                  <Tag
                    key={v}
                    style={{ cursor: 'pointer', fontSize: 11, margin: '2px 0' }}
                    onClick={() => insertVariable(v)}
                  >
                    {v}
                  </Tag>
                ))}
              </Space>
            </div>
          ))}
        </div>
      )}

      {/* Редактор */}
      <ReactQuill
        value={value}
        onChange={onChange}
        modules={modules}
        formats={formats}
        theme="snow"
        style={{ height, marginBottom: 40 }}
        className="template-quill-editor"
      />

      {/* Стили для Quill */}
      <style>{`
        .template-quill-editor .ql-container {
          height: ${height - 42}px;
          font-size: 13px;
        }
        .template-quill-editor .ql-editor {
          font-family: 'Segoe UI', Arial, sans-serif;
        }
        .template-quill-editor .ql-toolbar {
          background: #fafafa;
          border-radius: 6px 6px 0 0;
        }
        .template-quill-editor .ql-container {
          border-radius: 0 0 6px 6px;
        }
      `}</style>
    </div>
  )
}

export default TemplateEditor
