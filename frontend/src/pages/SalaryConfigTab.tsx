import React, { useState, useEffect } from 'react'
import {
  Card, Button, Input, InputNumber, Select, Table, Tag, Space,
  Modal, Form, message, Typography, Row, Col, Radio, Popconfirm, Divider, Alert, Checkbox
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined,
  CalculatorOutlined, ThunderboltOutlined
} from '@ant-design/icons'
import api from '../api'

const { Text, Title } = Typography

const SalaryConfigTab: React.FC = () => {
  const [configs, setConfigs] = useState<any[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<any>(null)
  const [form] = Form.useForm()
  const [configType, setConfigType] = useState('formula')
  const [previewValue, setPreviewValue] = useState<number | null>(null)
  const [previewInputs, setPreviewInputs] = useState({ total: 10000, parts: 3000, cash: 5000, card: 5000 })

  useEffect(() => { loadConfigs() }, [])

  const loadConfigs = async () => {
    try {
      const res = await api.get('/salary/config')
      setConfigs(res.data || [])
    } catch { message.error('Ошибка загрузки') }
  }

  const handleCreate = () => {
    setEditingConfig(null)
    setConfigType('formula')
    form.resetFields()
    form.setFieldsValue({ config_type: 'formula', period: 'per_order', is_active: false })
    setPreviewValue(null)
    setPreviewInputs({ total: 10000, parts: 3000, cash: 5000, card: 5000 })
    setModalOpen(true)
  }

  const handleEdit = (cfg: any) => {
    setEditingConfig(cfg)
    setConfigType(cfg.config_type || 'formula')
    form.setFieldsValue(cfg)
    setPreviewValue(null)
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    try {
      await api.post('/salary/config', values)
      message.success('Сохранено')
      setModalOpen(false)
      loadConfigs()
    } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') }
  }

  const handleActivate = async (id: number) => {
    try {
      await api.post(`/salary/config/${id}/activate`)
      message.success('Активировано')
      loadConfigs()
    } catch { message.error('Ошибка') }
  }

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/salary/config/${id}`)
      message.success('Удалено')
      loadConfigs()
    } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') }
  }

  const testFormula = () => {
    const formula = form.getFieldValue('formula_string')
    if (!formula) { message.warning('Введите формулу'); return }
    try {
      let f = formula
        .replace(/\{cash_net\}/g, String(previewInputs.cash))
        .replace(/\{card_net\}/g, String(previewInputs.card))
        .replace(/\{payments_net\}/g, String(previewInputs.cash + previewInputs.card))
        .replace(/cash_net/g, String(previewInputs.cash))
        .replace(/card_net/g, String(previewInputs.card))
        .replace(/payments_net/g, String(previewInputs.cash + previewInputs.card))
        .replace(/\{total_cost\}/g, String(previewInputs.total))
        .replace(/\{total\}/g, String(previewInputs.total))
        .replace(/\{parts_cost\}/g, String(previewInputs.parts))
        .replace(/\{parts\}/g, String(previewInputs.parts))
        .replace(/total_cost/g, String(previewInputs.total))
        .replace(/parts_cost/g, String(previewInputs.parts))
        .replace(/total/g, String(previewInputs.total))
        .replace(/parts/g, String(previewInputs.parts))
        .replace(/\{orders_count\}/g, '1')
        .replace(/\{base_salary\}/g, '0')
      const sanitized = f.replace(/[^0-9+\-*/().%\s]/g, '')
      const result = Function('"use strict"; return (' + sanitized + ')')()
      setPreviewValue(Math.round(Number(result)))
    } catch { message.error('Ошибка в формуле'); setPreviewValue(null) }
  }

  const columns = [
    { title: 'Название', dataIndex: 'name', key: 'name', render: (v: string, r: any) => <Text strong>{v || r.formula_string}</Text> },
    { title: 'Тип', key: 'type', width: 90, render: (_: any, r: any) => (
      <Tag color={r.config_type === 'fixed' ? 'blue' : 'green'}>{r.config_type === 'fixed' ? '💰 Фикс' : '📊 %'}</Tag>
    )},
    { title: 'Значение', key: 'value', width: 300, render: (_: any, r: any) => {
      if (r.config_type === 'fixed') return <Text>{r.fixed_amount} ₽ / {r.period}</Text>
      return <Text code style={{fontSize: 11}}>{r.formula_string}</Text>
    }},
    { title: 'Статус', key: 'active', width: 80, render: (_: any, r: any) => r.is_active ? <Tag color="green">✅</Tag> : <Tag>⏸️</Tag> },
    { title: 'Действия', key: 'actions', width: 160, render: (_: any, r: any) => (
      <Space size={4}>
        {!r.is_active && <Button size="small" onClick={() => handleActivate(r.id)}>Актив.</Button>}
        <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
        <Popconfirm title="Удалить?" onConfirm={() => handleDelete(r.id)}>
          <Button size="small" icon={<DeleteOutlined />} danger />
        </Popconfirm>
      </Space>
    )},
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>💰 Формулы зарплат</Title>
          <Text type="secondary">Создайте формулы и назначьте их сотрудникам в разделе "Сотрудники"</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>Добавить формулу</Button>
      </div>
      <Card size="small">
        <Table dataSource={configs} rowKey="id" columns={columns} pagination={false} size="small" locale={{ emptyText: 'Нет формул' }} />
      </Card>

      <Modal title={editingConfig ? 'Редактировать' : 'Добавить формулу'} open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} width={550}>
        <Form form={form} layout="vertical">
          <Form.Item label="Название" name="name" rules={[{required: true}]}>
            <Input placeholder="Мастер 40% / Приёмщик 4000₽" />
          </Form.Item>
          <Form.Item label="Тип" name="config_type" initialValue="formula">
            <Radio.Group onChange={e => { setConfigType(e.target.value); setPreviewValue(null) }}>
              <Radio.Button value="formula">📊 Формула (процент)</Radio.Button>
              <Radio.Button value="fixed">💰 Фиксированная</Radio.Button>
            </Radio.Group>
          </Form.Item>
          {configType === 'formula' && (
            <>
              <Form.Item label="Формула" name="formula_string" rules={[{required: true}]}>
                <Input.TextArea rows={2} placeholder="(total_cost - parts_cost) * 0.4" onChange={() => setPreviewValue(null)} />
              </Form.Item>
              <Alert message="Переменные: {cash_net} {card_net} {payments_net} {total_cost} {parts_cost} {orders_count} {base_salary}" type="info" showIcon style={{fontSize: 12, marginBottom: 12}} />

              {/* Тест формулы */}
              <Divider style={{margin: '12px 0'}}><Text type="secondary">⚡ Тест формулы</Text></Divider>
              <Row gutter={8}>
                <Col span={12}>
                  <Form.Item label="Нал (cash_net)" style={{marginBottom: 4}}>
                    <InputNumber value={previewInputs.cash} onChange={v => setPreviewInputs(p => ({...p, cash: v || 0}))} style={{width: '100%'}} suffix="₽" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="Карта (card_net)" style={{marginBottom: 4}}>
                    <InputNumber value={previewInputs.card} onChange={v => setPreviewInputs(p => ({...p, card: v || 0}))} style={{width: '100%'}} suffix="₽" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={8}>
                <Col span={11}>
                  <Form.Item label="Выручка" style={{marginBottom: 0}}>
                    <InputNumber value={previewInputs.total} onChange={v => setPreviewInputs(p => ({...p, total: v || 0}))} style={{width: '100%'}} suffix="₽" />
                  </Form.Item>
                </Col>
                <Col span={11}>
                  <Form.Item label="Запчасти" style={{marginBottom: 0}}>
                    <InputNumber value={previewInputs.parts} onChange={v => setPreviewInputs(p => ({...p, parts: v || 0}))} style={{width: '100%'}} suffix="₽" />
                  </Form.Item>
                </Col>
                <Col span={2} style={{display: 'flex', alignItems: 'flex-end'}}>
                  <Button icon={<ThunderboltOutlined />} onClick={testFormula} />
                </Col>
              </Row>
              {previewValue !== null && (
                <Alert message={`Зарплата мастера: ${previewValue.toLocaleString()} ₽`} type="success" showIcon style={{marginTop: 8}} />
              )}
            </>
          )}
          {configType === 'fixed' && (
            <>
              <Form.Item label="Сумма" name="fixed_amount" rules={[{required: true}]}>
                <InputNumber min={0} style={{width: '100%'}} suffix="₽" />
              </Form.Item>
              <Form.Item label="Период" name="period" initialValue="per_shift">
                <Select options={[{label: 'За заказ', value: 'per_order'}, {label: 'За смену', value: 'per_shift'}, {label: 'В месяц', value: 'per_month'}]} />
              </Form.Item>
            </>
          )}
          <Form.Item name="is_active" valuePropName="checked" initialValue={false}><Checkbox>Активная (используется по умолчанию)</Checkbox></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SalaryConfigTab
