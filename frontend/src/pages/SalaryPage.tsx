import React, { useState, useEffect } from 'react'
import { 
  Card, Button, Input, InputNumber, Select, Table, Tag, Space, 
  Modal, Form, message, Typography, Row, Col, Radio, Popconfirm, Divider, Alert, Checkbox
} from 'antd'
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined,
  CalculatorOutlined, DollarOutlined, ThunderboltOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Text, Title } = Typography

const salaryApi = axios.create({ baseURL: '/api/salary' })
salaryApi.interceptors.request.use(c => {
  const t = localStorage.getItem('token')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})

const PERIOD_LABELS: Record<string, string> = {
  per_order: 'За заказ',
  per_shift: 'За смену',
  per_month: 'В месяц',
}

const SalaryPage: React.FC = () => {
  const [configs, setConfigs] = useState<any[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<any>(null)
  const [form] = Form.useForm()
  const [configType, setConfigType] = useState('formula')
  const [previewValue, setPreviewValue] = useState<number | null>(null)
  const [previewInputs, setPreviewInputs] = useState({ total: 10000, parts: 3000 })

  useEffect(() => {
    loadConfigs()
  }, [])

  const loadConfigs = async () => {
    try {
      const res = await salaryApi.get('/config')
      setConfigs(res.data || [])
    } catch { message.error('Ошибка загрузки') }
  }

  const handleCreate = () => {
    setEditingConfig(null)
    setConfigType('formula')
    form.resetFields()
    form.setFieldsValue({ config_type: 'formula', period: 'per_order', is_active: false })
    setPreviewValue(null)
    setModalOpen(true)
  }

  const handleEdit = (cfg: any) => {
    setEditingConfig(cfg)
    setConfigType(cfg.config_type || 'formula')
    form.setFieldsValue({
      name: cfg.name,
      config_type: cfg.config_type,
      formula_string: cfg.formula_string,
      fixed_amount: cfg.fixed_amount,
      period: cfg.period,
      description: cfg.description,
      is_active: cfg.is_active,
    })
    setPreviewValue(null)
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    try {
      await salaryApi.post('/config', values)
      message.success(editingConfig ? 'Конфигурация обновлена' : 'Конфигурация создана')
      setModalOpen(false)
      form.resetFields()
      loadConfigs()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const handleActivate = async (id: number) => {
    try {
      await salaryApi.post(`/config/${id}/activate`)
      message.success('Активировано')
      loadConfigs()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await salaryApi.delete(`/config/${id}`)
      message.success('Удалено')
      loadConfigs()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка удаления')
    }
  }

  const testFormula = () => {
    const formula = form.getFieldValue('formula_string')
    if (!formula) { message.warning('Введите формулу'); return }
    
    try {
      let f = formula
        .replace(/\{total_cost\}/g, String(previewInputs.total))
        .replace(/\{total\}/g, String(previewInputs.total))
        .replace(/\{parts_cost\}/g, String(previewInputs.parts))
        .replace(/\{parts\}/g, String(previewInputs.parts))
        .replace(/\{base_salary\}/g, String(form.getFieldValue('fixed_amount') || 0))
      
      const sanitized = f.replace(/[^0-9+\-*/().%\s]/g, '')
      const result = Function('"use strict"; return (' + sanitized + ')')()
      setPreviewValue(Math.round(Number(result)))
    } catch {
      message.error('Ошибка в формуле')
      setPreviewValue(null)
    }
  }

  const columns = [
    { title: 'Название', key: 'name', render: (_: any, r: any) => (
      <Space><CalculatorOutlined /> <Text strong>{r.name || r.formula_string}</Text></Space>
    )},
    { title: 'Тип', key: 'type', width: 90, render: (_: any, r: any) => (
      <Tag color={r.config_type === 'fixed' ? 'blue' : 'green'}>
        {r.config_type === 'fixed' ? '💰 Фикс' : '📊 %'}
      </Tag>
    )},
    { title: 'Значение', key: 'value', width: 250, render: (_: any, r: any) => {
      if (r.config_type === 'fixed') {
        return <Text>{r.fixed_amount?.toLocaleString()} ₽ <Text type="secondary">/ {PERIOD_LABELS[r.period] || r.period}</Text></Text>
      }
      return <Text code style={{fontSize: 12}}>{r.formula_string}</Text>
    }},
    { title: 'Статус', key: 'active', width: 80, render: (_: any, r: any) => (
      r.is_active ? <Tag color="green">✅</Tag> : <Tag color="default">⏸️</Tag>
    )},
    { title: 'Действия', key: 'actions', width: 180, render: (_: any, r: any) => (
      <Space size={4}>
        {!r.is_active && <Button size="small" icon={<CheckCircleOutlined />} onClick={() => handleActivate(r.id)}>Акт.</Button>}
        <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
        <Popconfirm title="Удалить?" onConfirm={() => handleDelete(r.id)}>
          <Button size="small" icon={<DeleteOutlined />} danger />
        </Popconfirm>
      </Space>
    )},
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0 }}>💰 Настройка зарплат</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>Добавить</Button>
      </div>

      <Card size="small">
        <Table 
          dataSource={configs} 
          rowKey="id" 
          columns={columns} 
          pagination={false} 
          size="small" 
          locale={{ emptyText: 'Нет настроек. Нажмите «Добавить»' }}
        />
      </Card>

      <Modal
        title={editingConfig ? 'Редактировать' : 'Добавить формулу/фикс'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={550}
        okText={editingConfig ? 'Сохранить' : 'Создать'}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="Название" name="name" rules={[{required: true, message: 'Введите название'}]}>
            <Input placeholder="Мастер 40% / Приёмщик 4000₽" />
          </Form.Item>

          <Form.Item label="Тип расчёта" name="config_type" initialValue="formula">
            <Radio.Group onChange={e => { setConfigType(e.target.value); setPreviewValue(null) }}>
              <Radio.Button value="formula">📊 Формула (процент)</Radio.Button>
              <Radio.Button value="fixed">💰 Фиксированная</Radio.Button>
            </Radio.Group>
          </Form.Item>

          {configType === 'formula' && (
            <>
              <Form.Item label="Формула" name="formula_string" rules={[{required: configType === 'formula', message: 'Введите формулу'}]}>
                <Input.TextArea 
                  rows={2} 
                  placeholder="(total_cost - parts_cost) * 0.4"
                  onChange={() => setPreviewValue(null)}
                />
              </Form.Item>
              <Alert 
                message="Переменные: {total_cost} {parts_cost} {orders_count} {base_salary}"
                type="info" 
                showIcon 
                style={{fontSize: 12, marginBottom: 12}}
              />

              {/* Тест формулы */}
              <Divider style={{margin: '12px 0'}}><Text type="secondary">Тест формулы</Text></Divider>
              <Row gutter={8}>
                <Col span={11}>
                  <Form.Item label="Выручка" style={{marginBottom: 8}}>
                    <InputNumber 
                      value={previewInputs.total} 
                      onChange={v => setPreviewInputs(p => ({...p, total: v || 0}))} 
                      style={{width: '100%'}} 
                    />
                  </Form.Item>
                </Col>
                <Col span={11}>
                  <Form.Item label="Запчасти" style={{marginBottom: 8}}>
                    <InputNumber 
                      value={previewInputs.parts} 
                      onChange={v => setPreviewInputs(p => ({...p, parts: v || 0}))} 
                      style={{width: '100%'}} 
                    />
                  </Form.Item>
                </Col>
                <Col span={2} style={{display: 'flex', alignItems: 'flex-end'}}>
                  <Button icon={<ThunderboltOutlined />} onClick={testFormula} />
                </Col>
              </Row>
              {previewValue !== null && (
                <Alert 
                  message={`Результат: ${previewValue.toLocaleString()} ₽`} 
                  type="success" 
                  showIcon 
                />
              )}
            </>
          )}

          {configType === 'fixed' && (
            <>
              <Form.Item label="Сумма" name="fixed_amount" rules={[{required: configType === 'fixed', message: 'Введите сумму'}]}>
                <InputNumber min={0} style={{width: '100%'}} placeholder="4000" suffix="₽" />
              </Form.Item>
              <Form.Item label="Период" name="period" initialValue="per_shift">
                <Select options={[
                  {label: 'За каждый заказ', value: 'per_order'},
                  {label: 'За смену', value: 'per_shift'},
                  {label: 'В месяц', value: 'per_month'},
                ]} />
              </Form.Item>
            </>
          )}

          <Form.Item label="Описание" name="description">
            <Input placeholder="Описание..." />
          </Form.Item>

          <Form.Item name="is_active" valuePropName="checked" initialValue={false}>
            <Checkbox>Активная (используется по умолчанию)</Checkbox>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SalaryPage
