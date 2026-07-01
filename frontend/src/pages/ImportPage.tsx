import React, { useState } from 'react'
import { 
  Card, Steps, Upload, Select, Button, Table, message, Alert, 
  Space, Tag, Descriptions, Typography, Row, Col, Spin, Progress 
} from 'antd'
import { 
  InboxOutlined, ArrowRightOutlined, ArrowLeftOutlined, 
  CheckCircleOutlined, CloseCircleOutlined, ImportOutlined 
} from '@ant-design/icons'
import axios from 'axios'

const { Dragger } = Upload
const { Text, Title } = Typography

const api = axios.create({ baseURL: '/api/settings' })
api.interceptors.request.use(c => {
  const t = localStorage.getItem('token')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})

const IMPORT_TYPES = {
  clients: 'Клиенты',
  parts: 'Запчасти',
  orders: 'Заказы',
}

const ImportPage: React.FC = () => {
  const [step, setStep] = useState(0)
  const [importType, setImportType] = useState('clients')
  const [fileData, setFileData] = useState<any>(null)
  const [fieldMapping, setFieldMapping] = useState<Record<string, string>>({})
  const [availableFields, setAvailableFields] = useState<Record<string, string>>({})
  const [previewRows, setPreviewRows] = useState<any[]>([])
  const [fileHeaders, setFileHeaders] = useState<string[]>([])
  const [importResult, setImportResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  // Шаг 1: Загрузка файла
  const handleUpload = async (file: any) => {
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('import_type', importType)
      const res = await api.post('/import/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setFileData(res.data)
      setFileHeaders(res.data.headers)
      setPreviewRows(res.data.rows.slice(0, 5))

      // Fetch available fields for mapping
      const previewRes = await api.post('/import/preview', {
        import_type: importType,
        headers: res.data.headers,
      })
      setAvailableFields(previewRes.data.available_fields || {})

      setStep(1)
      message.success(`Файл загружен: ${res.data.total_rows} строк`)
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка загрузки')
    }
    setLoading(false)
  }

  // Шаг 2: Маппинг полей
  const handleFieldChange = (dbField: string, fileField: string) => {
    setFieldMapping(prev => ({ ...prev, [dbField]: fileField }))
  }

  const handleNextMapping = async () => {
    try {
      await api.post('/import/validate', {
        import_type: importType,
        file_headers: fileHeaders,
        field_mapping: fieldMapping,
      })
      setStep(2)
    } catch (e: any) {
      const errors = e.response?.data?.errors || ['Ошибка валидации']
      message.error(errors.join(', '))
    }
  }

  // Шаг 3: Предпросмотр и импорт
  const handleImport = async () => {
    setLoading(true)
    try {
      const res = await api.post('/import/execute', {
        import_type: importType,
        field_mapping: fieldMapping,
        rows: fileData.rows,
      })
      setImportResult(res.data)
      setStep(3)
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка импорта')
    }
    setLoading(false)
  }

  const reset = () => {
    setStep(0); setFileData(null); setFieldMapping({}); setPreviewRows([]); setImportResult(null);
  }

  return (
    <div>
      <Title level={3}><ImportOutlined /> Импорт данных</Title>

      <Steps current={step} style={{ marginBottom: 24 }} items={[
        { title: 'Загрузка файла' },
        { title: 'Маппинг полей' },
        { title: 'Проверка' },
        { title: 'Результат' },
      ]} />

      {/* Шаг 0: Загрузка */}
      {step === 0 && (
        <Card>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Text strong>Тип импорта: </Text>
              <Select value={importType} onChange={setImportType} style={{ width: 200 }}>
                {Object.entries(IMPORT_TYPES).map(([k, v]) => <Select.Option key={k} value={k}>{v}</Select.Option>)}
              </Select>
            </div>
            <Dragger customRequest={({ file }) => handleUpload(file)} accept=".csv,.xlsx,.xls,.txt">
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">Загрузите файл для импорта</p>
              <p className="ant-upload-hint">CSV, XLSX, XLS, TXT (макс. 10 МБ)</p>
            </Dragger>
            <Alert type="info" message="Советы" description={
              <ul style={{ margin: 0 }}>
                <li>Первая строка должна содержать заголовки</li>
                <li>CSV: автоопределение разделителя (табуляция, ;, ,, |)</li>
                <li>При импорте клиентов обязательны: ФИО или телефон</li>
                <li>При импорте запчастей обязательно: Название</li>
              </ul>
            } />
          </Space>
        </Card>
      )}

      {/* Шаг 1: Маппинг */}
      {step === 1 && fileData && (
        <Card>
          <Title level={4}>Сопоставление полей</Title>
          <Text type="secondary">Для каждого поля CRM выберите колонку из файла</Text>
          <div style={{ marginTop: 16 }}>
            {Object.entries(availableFields).map(([dbField, label]) => (
              <div key={dbField} style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 12 }}>
                <Tag color="blue" style={{ minWidth: 160 }}>{label}</Tag>
                <span>←</span>
                <Select
                  value={fieldMapping[dbField] || undefined}
                  onChange={(v) => handleFieldChange(dbField, v)}
                  style={{ width: 250 }}
                  allowClear
                  placeholder="Колонка из файла"
                >
                  {fileHeaders.map((h: string) => (
                    <Select.Option key={h} value={h}>{h}</Select.Option>
                  ))}
                </Select>
              </div>
            ))}
          </div>
          <Button type="primary" onClick={handleNextMapping} icon={<ArrowRightOutlined />}>Далее → Проверка</Button>
        </Card>
      )}

      {/* Шаг 2: Предпросмотр */}
      {step === 2 && previewRows.length > 0 && (
        <Card>
          <Title level={4}>Предпросмотр данных ({fileData.total_rows} строк)</Title>
          <Table dataSource={previewRows} rowKey={(_, i) => i ?? 0} pagination={false} size="small"
            columns={fileHeaders.map(h => ({ title: h, dataIndex: h, key: h, ellipsis: true }))}
          />
          <Space style={{ marginTop: 16 }}>
            <Button onClick={() => setStep(1)} icon={<ArrowLeftOutlined />}>Назад</Button>
            <Button type="primary" onClick={handleImport} icon={<ImportOutlined />} loading={loading}>
              Импортировать {fileData.total_rows} записей
            </Button>
          </Space>
        </Card>
      )}

      {/* Шаг 3: Результат */}
      {step === 3 && importResult && (
        <Card>
          <Title level={4}>Результат импорта</Title>
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={5}><Card><div style={{ textAlign: 'center' }}><CheckCircleOutlined style={{ fontSize: 32, color: '#52c41a' }} /><br /><Text strong>Создано</Text><br /><Title level={2} style={{ margin: 0, color: '#52c41a' }}>{importResult.created}</Title></div></Card></Col>
            <Col span={5}><Card><div style={{ textAlign: 'center' }}><CloseCircleOutlined style={{ fontSize: 32, color: '#f5222d' }} /><br /><Text strong>Ошибок</Text><br /><Title level={2} style={{ margin: 0, color: '#f5222d' }}>{importResult.errors}</Title></div></Card></Col>
            <Col span={5}><Card><div style={{ textAlign: 'center' }}><Text style={{ fontSize: 32 }}>⏭️</Text><br /><Text strong>Пропущено</Text><br /><Title level={2} style={{ margin: 0, color: '#faad14' }}>{importResult.skipped}</Title></div></Card></Col>
            <Col span={5}><Card><div style={{ textAlign: 'center' }}><Text style={{ fontSize: 32 }}>🔄</Text><br /><Text strong>Дубликатов</Text><br /><Title level={2} style={{ margin: 0, color: '#1890ff' }}>{importResult.duplicates || 0}</Title></div></Card></Col>
            <Col span={4}><Card><div style={{ textAlign: 'center' }}><Progress type="circle" percent={fileData.total_rows > 0 ? Math.round(importResult.created / fileData.total_rows * 100) : 0} /><br /><Text strong>Успешность</Text></div></Card></Col>
          </Row>
          {importResult.details && importResult.details.length > 0 && (
            <Alert type="warning" style={{ marginTop: 16 }} message="Детали" description={
              <ul style={{ maxHeight: 200, overflowY: 'auto' }}>{importResult.details.map((d: string, i: number) => <li key={i}>{d}</li>)}</ul>
            } />
          )}
          <Button type="primary" onClick={reset} style={{ marginTop: 16 }} icon={<ImportOutlined />}>Новый импорт</Button>
        </Card>
      )}

      {loading && <Spin tip="Загрузка..." style={{ display: 'block', textAlign: 'center', marginTop: 40 }} />}
    </div>
  )
}

// Маппинг полей для UI
export default ImportPage
