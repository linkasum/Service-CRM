import React, { useState, useEffect } from 'react'
import {
  Form, Input, Select, Button, Row, Col, Card, Checkbox, message, Space,
  Typography, Divider, InputNumber, Spin
} from 'antd'
import { ArrowLeftOutlined, SaveOutlined, UserOutlined, PhoneOutlined, MailOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { createOrder, getClients, getUsers, searchClientByPhone, getBrands, createBrand, getCategories, createCategory, getDeviceModels, createDeviceModel, getAccessoryTemplates, createAccessoryTemplate } from '../api'
import api from '../api'
import { useTheme } from '../contexts/ThemeContext'

const { Title, Text } = Typography
const { TextArea } = Input

const DEVICE_CATEGORIES = [
  { value: 'phone', label: '📱 Телефон' },
  { value: 'laptop', label: '💻 Ноутбук' },
  { value: 'tablet', label: '📱 Планшет' },
  { value: 'pc', label: '🖥️ ПК' },
  { value: 'console', label: '🎮 Консоль' },
  { value: 'other', label: '🔧 Другое' },
]

const ACCESSORIES = [
  { value: 'none', label: 'Без аксессуаров' },
  { value: 'charger', label: 'Зарядка' },
  { value: 'case', label: 'Чехол' },
  { value: 'headphones', label: 'Наушники' },
  { value: 'full', label: 'Полная комплектация' },
]

const ORDER_SOURCES_DEFAULT = [
  { value: 'Прямой визит', label: 'Прямой визит' },
  { value: 'Google', label: 'Google' },
  { value: 'Яндекс', label: 'Яндекс' },
  { value: 'Instagram', label: 'Instagram' },
  { value: 'Telegram', label: 'Telegram' },
  { value: 'Рекомендация', label: 'Рекомендация' },
  { value: 'Другое', label: 'Другое' },
]

const ORDER_AGE_GROUPS_DEFAULT = [
  { value: '18-25', label: '18-25' },
  { value: '25-35', label: '25-35' },
  { value: '35-45', label: '35-45' },
  { value: '45+', label: '45+' },
]

const OrderCreatePage: React.FC = () => {
  const navigate = useNavigate()
  const { mode } = useTheme()
  const isDark = mode === 'dark'
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<any[]>([])
  const [users, setUsers] = useState<any[]>([])
  const [sources, setSources] = useState<any[]>([])
  const [ageGroups, setAgeGroups] = useState<any[]>([])
  const [documentsToPrint, setDocumentsToPrint] = useState<string[]>([])
  const [clientFound, setClientFound] = useState<boolean>(false)
  const [clientLoading, setClientLoading] = useState<boolean>(false)
  const [foundClients, setFoundClients] = useState<any[]>([])
  const [showClientDropdown, setShowClientDropdown] = useState<boolean>(false)
  
  // Бренды и категории
  const [brands, setBrands] = useState<any[]>([])
  const [categories, setCategories] = useState<any[]>([])
  const [brandSearch, setBrandSearch] = useState<string>('')
  const [categorySearch, setCategorySearch] = useState<string>('')
  
  // Модели устройств
  const [deviceModels, setDeviceModels] = useState<any[]>([])
  const [selectedBrandId, setSelectedBrandId] = useState<number | undefined>(undefined)
  const [modelSearch, setModelSearch] = useState<string>('')
  const [showModelDropdown, setShowModelDropdown] = useState<boolean>(false)
  
  // Комплектации
  const [accessoryTemplates, setAccessoryTemplates] = useState<any[]>([])
  const [accessorySearch, setAccessorySearch] = useState<string>('')

  useEffect(() => {
    loadClients()
    loadUsers()
    loadBrands()
    loadCategories()
    loadAccessoryTemplates()
    loadSources()
    loadAgeGroups()
  }, [])

  // Закрытие dropdown при клике вне
  useEffect(() => {
    const handleClickOutside = () => {
      if (showClientDropdown) {
        setShowClientDropdown(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [showClientDropdown])

  const loadClients = async () => {
    try {
      const data = await getClients()
      // API возвращает {clients: [...], total: N}
      const clientsList = data.clients || data.items || data || []
      console.log('📥 Загружено клиентов:', clientsList.length)
      setClients(clientsList)
    } catch (err) {
      console.error('❌ Ошибка загрузки клиентов:', err)
      setClients([])
    }
  }

  const loadUsers = async () => {
    try {
      const data = await getUsers()
      setUsers(data.items || data)
    } catch {}
  }

  const loadBrands = async () => {
    try {
      const data = await getBrands()
      setBrands(data || [])
    } catch {}
  }

  const loadCategories = async () => {
    try {
      const data = await getCategories()
      setCategories(data || [])
    } catch {}
  }

  // Загрузка моделей для выбранного бренда
  const loadDeviceModels = async (brandId?: number) => {
    if (!brandId) {
      setDeviceModels([])
      return
    }
    try {
      const data = await getDeviceModels({ brand_id: brandId })
      setDeviceModels(data || [])
      console.log(`📥 Загружено моделей: ${data.length}`)
    } catch (err) {
      console.error('❌ Ошибка загрузки моделей:', err)
      setDeviceModels([])
    }
  }

  // Создание новой модели
  const handleCreateModel = async (modelName: string) => {
    if (!modelName.trim() || !selectedBrandId) return null
    try {
      const newModel = await createDeviceModel({
        name: modelName.trim(),
        brand_id: selectedBrandId,
      })
      setDeviceModels(prev => [...prev, newModel])
      message.success(`Модель "${modelName}" создана`)
      return newModel
    } catch {
      message.error('Ошибка создания модели')
      return null
    }
  }

  // Загрузка комплектаций
  const loadAccessoryTemplates = async () => {
    try {
      const data = await getAccessoryTemplates()
      setAccessoryTemplates(data || [])
      console.log(`📦 Загружено комплектаций: ${data.length}`)
    } catch (err) {
      console.error('❌ Ошибка загрузки комплектаций:', err)
      setAccessoryTemplates([])
    }
  }

  const loadSources = async () => {
    try {
      const res = await api.get('/settings/client-sources')
      setSources((res.data || []).map((s: any) => ({ value: s.name, label: s.name })))
    } catch { setSources(ORDER_SOURCES_DEFAULT) }
  }

  const loadAgeGroups = async () => {
    try {
      const res = await api.get('/settings/age-groups')
      setAgeGroups((res.data || []).map((a: any) => ({ value: a.name, label: a.name })))
    } catch { setAgeGroups(ORDER_AGE_GROUPS_DEFAULT) }
  }

  // Создание новой комплектации
  const handleCreateAccessory = async (accessoryName: string) => {
    if (!accessoryName.trim()) return null
    try {
      const newAccessory = await createAccessoryTemplate({
        name: accessoryName.trim(),
      })
      setAccessoryTemplates(prev => [...prev, newAccessory])
      message.success(`Комплектация "${accessoryName}" создана`)
      return newAccessory
    } catch {
      message.error('Ошибка создания комплектации')
      return null
    }
  }

  // Создание нового бренда
  const handleCreateBrand = async (name: string) => {
    if (!name.trim()) return null
    try {
      const newBrand = await createBrand(name.trim())
      setBrands(prev => [...prev, newBrand])
      message.success(`Бренд "${name}" создан`)
      return newBrand
    } catch {
      message.error('Ошибка создания бренда')
      return null
    }
  }

  // Создание новой категории
  const handleCreateCategory = async (name: string) => {
    if (!name.trim()) return null
    try {
      const newCategory = await createCategory(name.trim())
      setCategories(prev => [...prev, newCategory])
      message.success(`Категория "${name}" создана`)
      return newCategory
    } catch {
      message.error('Ошибка создания категории')
      return null
    }
  }

  // Обработчик изменения значения телефона
  const handlePhoneChange = (phone: string) => {
    console.log('📞 Поиск клиента по телефону:', phone)
    
    if (phone && phone.length >= 5) {
      setClientLoading(true)
      setClientFound(false)
      setShowClientDropdown(false)
      
      // Нормализуем телефон для поиска
      // Заменяем 8 в начале на +7, удаляем все разделители
      const normalizePhone = (p: string) => {
        let normalized = p.replace(/\D/g, '')
        // 89161234567 -> 79161234567
        if (normalized.startsWith('8') && normalized.length === 11) {
          normalized = '7' + normalized.substring(1)
        }
        // 9161234567 -> 79161234567
        else if (normalized.length === 10) {
          normalized = '7' + normalized
        }
        return normalized
      }
      const searchPhone = normalizePhone(phone)
      
      console.log('🔍 Нормализованный телефон для поиска:', searchPhone)
      console.log('📋 Клиентов в базе:', clients.length)
      
      // Ищем всех подходящих клиентов
      const matches = clients.filter((c: any) => {
        const cp = normalizePhone(c.phone || '')
        const match = cp === searchPhone || cp.includes(searchPhone) || searchPhone.includes(cp)
        if (match) {
          console.log('✅ Найден клиент:', c.name, c.phone, '->', cp)
        }
        return match
      })
      
      if (matches.length > 0) {
        console.log('✅ Найдено клиентов:', matches.length)
        setFoundClients(matches)
        setShowClientDropdown(true)
        setClientLoading(false)
      } else {
        console.log('🌐 Клиенты не найдены')
        setFoundClients([])
        setShowClientDropdown(false)
        setClientLoading(false)
      }
    } else {
      setClientFound(false)
      setClientLoading(false)
      setShowClientDropdown(false)
      setFoundClients([])
    }
  }

  // Выбор клиента из списка
  const handleClientSelect = (client: any) => {
    console.log('👤 Выбран клиент:', client.name)
    setClientFound(true)
    setShowClientDropdown(false)
    form.setFieldsValue({
      client_name: client.name,
      client_email: client.email,
      source: client.source,
      age_group: client.age_group,
    })
  }

  const handleSubmit = async () => {
    // Защита от повторной отправки
    if (loading) {
      console.log('⏳ Уже идёт создание заказа...')
      return
    }

    try {
      const values = await form.validateFields()
      setLoading(true)

      console.log('📦 Создаём заказ:', values)

      // Преобразуем device_brand из ID в название
      const brand = brands.find(b => b.id === values.device_brand)
      const deviceBrandName = brand ? brand.name : (values.device_brand || '')

      // Преобразуем accessories из массива в JSON строку
      const accessoriesString = values.accessories ? JSON.stringify(values.accessories) : ''

      // Создаём заказ
      const order = await createOrder({
        ...values,
        device_brand: deviceBrandName,
        accessories: accessoriesString,
        appearance: values.appearance || 'Б/У',
        is_warranty: values.is_warranty || false,
        has_delivery: values.has_delivery || false,
      })

      console.log('✅ Заказ создан:', order.id)
      message.success('Заказ создан')

      // Печать документов — через <a> клик чтобы обойти popup blocker
      const docTypes: Record<string, string> = {
        receipt: 'receipt',
        diagnostic: 'diagnostic_act',
        work_act: 'work_act',
        invoice: 'invoice',
      }
      const token = localStorage.getItem('token') || ''

      for (const docType of documentsToPrint) {
        const templateType = docTypes[docType]
        if (templateType) {
          const url = `/api/documents/print/${order.id}/${templateType}?token=${token}`
          const a = document.createElement('a')
          a.href = url
          a.target = '_blank'
          a.rel = 'noopener noreferrer'
          a.click()
        }
      }

      navigate(`/orders/${order.id}`)
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка создания заказа')
    } finally {
      setLoading(false)
    }
  }

  const bg = isDark ? '#1a1a2e' : '#fff'
  const borderColor = isDark ? '#2a2a4a' : '#e8e8e8'
  const textColor = isDark ? '#e8e8e8' : '#1a1a1a'
  const labelColor = isDark ? '#999' : '#666'

  return (
    <div style={{ background: bg, minHeight: '100vh', padding: '16px 24px' }}>
      {/* Шапка */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/orders')} 
            style={{ background: isDark ? '#2a2a4a' : '#f5f5f5', border: `1px solid ${borderColor}`, color: textColor }} />
          <Title level={4} style={{ margin: 0, color: textColor }}>Новый заказ</Title>
        </Space>
        <Space>
          <Button type="primary" size="large" icon={<SaveOutlined />} onClick={handleSubmit} loading={loading} disabled={loading}>
            {loading ? 'Создание...' : 'Создать'}
          </Button>
        </Space>
      </div>

      <Form form={form} layout="vertical" style={{ maxWidth: 1200 }}
        onValuesChange={(changedValues) => {
          if (changedValues?.client_phone) {
            handlePhoneChange(changedValues.client_phone)
          }
        }}
      >
        <Row gutter={24}>
          {/* ЛЕВАЯ КОЛОНКА — Клиент */}
          <Col span={12}>
            <Card size="small" title={<Space><UserOutlined /> Клиент</Space>} style={{ background: bg, border: `1px solid ${borderColor}`, overflow: "visible" }} styles={{ body: { overflow: "visible", padding: "16px" } }}>
              <div style={{ position: 'relative' }}>
                <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Телефон *</Text>} name="client_phone" rules={[{ required: true, message: 'Введите телефон' }]}
                  getValueFromEvent={(e) => {
                    let val = e.target.value
                    let cleaned = val.replace(/[^\d+]/g, '')
                    if (/^8\d/.test(cleaned)) {
                      return '+7' + cleaned.substring(1)
                    }
                    return val
                  }}>
                  <Input
                    placeholder="+7 (999) 123-45-67"
                    suffix={
                      clientLoading ? (
                        <Spin size="small" />
                      ) : clientFound ? (
                        <CheckCircleOutlined style={{ color: '#52c41a' }} title="Клиент выбран" />
                      ) : null
                    }
                    autoComplete="off"
                  />
                </Form.Item>
                
                {/* Выпадающий список клиентов */}
                {showClientDropdown && foundClients.length > 0 && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      background: isDark ? '#1a1a2e' : '#fff',
                      border: `1px solid ${borderColor}`,
                      borderRadius: 6,
                      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                      zIndex: 1000,
                      maxHeight: 250,
                      overflowY: 'auto',
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    {foundClients.map((client: any) => (
                      <div
                        key={client.id}
                        onClick={() => handleClientSelect(client)}
                        style={{
                          padding: '8px 12px',
                          cursor: 'pointer',
                          borderBottom: `1px solid ${borderColor}`,
                          transition: 'background 0.2s',
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = isDark ? '#2a2a4a' : '#f5f5f5'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                      >
                        <div style={{ fontWeight: 600, fontSize: 13 }}>{client.name}</div>
                        <div style={{ fontSize: 12, opacity: 0.7 }}>{client.phone}{client.email ? ` • ${client.email}` : ''}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Имя *</Text>} name="client_name" rules={[{ required: true }]}>
                <Input placeholder="Иванов Иван" />
              </Form.Item>

              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Почта</Text>} name="client_email">
                    <Input placeholder="email@mail.ru" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Тип клиента</Text>} name="client_type" initialValue="individual">
                    <Select options={[
                      { label: 'Физ. лицо', value: 'individual' },
                      { label: 'Юр. лицо', value: 'legal' },
                    ]} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Возраст</Text>} name="age_group">
                    <Select options={ageGroups.length > 0 ? ageGroups : ORDER_AGE_GROUPS_DEFAULT} allowClear placeholder="—" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Откуда узнал</Text>} name="source">
                    <Select options={sources.length > 0 ? sources : ORDER_SOURCES_DEFAULT} allowClear placeholder="—" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Комментарий</Text>} name="comment">
                <TextArea rows={2} placeholder="Дополнительная информация..." />
              </Form.Item>
            </Card>
          </Col>

          {/* ПРАВАЯ КОЛОНКА — Устройство */}
          <Col span={12}>
            <Card size="small" title={<Space>📱 Устройство</Space>} style={{ background: bg, border: `1px solid ${borderColor}`, overflow: "visible" }} styles={{ body: { overflow: "visible", padding: "16px" } }}>
              <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Вид устройства *</Text>} name="device_category" rules={[{ required: true }]} initialValue="phone">
                <Select
                  options={categories.map(c => ({ value: c.name, label: c.name }))}
                  showSearch
                  filterOption={(input, option) =>
                    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  onSearch={setCategorySearch}
                  onChange={(value) => {
                    // Если ввели новое значение которого нет в списке
                    if (value && !categories.find(c => c.name === value)) {
                      handleCreateCategory(value).then(() => {
                        form.setFieldValue('device_category', value)
                      })
                    }
                  }}
                  notFoundContent={
                    categorySearch ? (
                      <div style={{ padding: 8, textAlign: 'center' }}>
                        <Button type="link" onClick={() => {
                          handleCreateCategory(categorySearch).then(() => {
                            form.setFieldValue('device_category', categorySearch)
                          })
                        }}>+ Создать "{categorySearch}"</Button>
                      </div>
                    ) : null
                  }
                />
              </Form.Item>

              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Бренд</Text>} name="device_brand">
                    <Select
                      options={brands.map(b => ({ value: b.id, label: b.name }))}
                      showSearch
                      allowClear
                      filterOption={(input, option) =>
                        (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                      }
                      onSearch={setBrandSearch}
                      onChange={(value, option) => {
                        setSelectedBrandId(value)
                        loadDeviceModels(value)
                        // Если ввели новое значение которого нет в списке
                        if (value && !brands.find(b => b.id === value)) {
                          handleCreateBrand(option?.label || brandSearch).then((newBrand) => {
                            if (newBrand) {
                              setSelectedBrandId(newBrand.id)
                              form.setFieldValue('device_brand', newBrand.id)
                              loadDeviceModels(newBrand.id)
                            }
                          })
                        }
                      }}
                      notFoundContent={
                        brandSearch ? (
                          <div style={{ padding: 8, textAlign: 'center' }}>
                            <Button type="link" onClick={() => {
                              handleCreateBrand(brandSearch).then((newBrand) => {
                                if (newBrand) {
                                  setSelectedBrandId(newBrand.id)
                                  form.setFieldValue('device_brand', newBrand.id)
                                  loadDeviceModels(newBrand.id)
                                }
                              })
                            }}>+ Создать бренд "{brandSearch}"</Button>
                          </div>
                        ) : null
                      }
                      placeholder="—"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Модель *</Text>} name="device_model" rules={[{ required: true }]}>
                    <Select
                      options={deviceModels.map(m => ({ value: m.name, label: m.name }))}
                      showSearch
                      allowClear
                      filterOption={(input, option) =>
                        (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                      }
                      onSearch={setModelSearch}
                      onChange={(value) => {
                        // Если ввели новое значение которого нет в списке
                        if (value && !deviceModels.find(m => m.name === value)) {
                          handleCreateModel(value).then(() => {
                            form.setFieldValue('device_model', value)
                          })
                        }
                      }}
                      notFoundContent={
                        modelSearch && selectedBrandId ? (
                          <div style={{ padding: 8, textAlign: 'center' }}>
                            <Button type="link" onClick={() => {
                              handleCreateModel(modelSearch).then(() => {
                                form.setFieldValue('device_model', modelSearch)
                              })
                            }}>+ Создать модель "{modelSearch}"</Button>
                          </div>
                        ) : modelSearch && !selectedBrandId ? (
                          <div style={{ padding: 8, textAlign: 'center', fontSize: 12, color: '#999' }}>
                            Сначала выберите бренд
                          </div>
                        ) : null
                      }
                      placeholder="—"
                      disabled={!selectedBrandId}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Серийный номер</Text>} name="serial_number">
                    <Input placeholder="SN123456" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Комплектация</Text>} name="accessories">
                    <Select
                      mode="multiple"
                      options={accessoryTemplates.map(a => ({ value: a.name, label: a.name }))}
                      showSearch
                      filterOption={(input, option) =>
                        (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                      }
                      onSearch={setAccessorySearch}
                      placeholder="Выберите комплектации"
                      maxTagCount="responsive"
                      allowClear
                      notFoundContent={
                        accessorySearch ? (
                          <div style={{ padding: 8, textAlign: 'center' }}>
                            <Button type="link" onClick={() => {
                              handleCreateAccessory(accessorySearch).then(() => {
                                form.setFieldValue('accessories', [...(form.getFieldValue('accessories') || []), accessorySearch])
                              })
                            }}>+ Создать комплектацию "{accessorySearch}"</Button>
                          </div>
                        ) : null
                      }
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Внешний вид</Text>} name="appearance" initialValue="Б/У">
                    <Select
                      options={[
                        { value: 'Б/У', label: 'Б/У' },
                        { value: 'Новый', label: 'Новый' },
                        { value: 'Как новый', label: 'Как новый' },
                        { value: 'С царапинами', label: 'С царапинами' },
                        { value: 'С повреждениями', label: 'С повреждениями' },
                        { value: 'Следы эксплуатации', label: 'Следы эксплуатации' },
                      ]}
                      allowClear
                      placeholder="—"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Описание проблемы *</Text>} name="complaint" rules={[{ required: true }]}>
                <TextArea rows={3} placeholder="Не включается, разбит экран..." />
              </Form.Item>
            </Card>
          </Col>
        </Row>

        <Divider style={{ borderColor, margin: '16px 0' }} />

        {/* НИЖНЯЯ ЧАСТЬ — Параметры */}
        <Row gutter={24}>
          <Col span={8}>
            <Card size="small" title="⚙️ Параметры" style={{ background: bg, border: `1px solid ${borderColor}`, overflow: "visible" }} styles={{ body: { overflow: "visible", padding: "16px" } }}>
              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Диагностика (дн.)</Text>} name="diagnostics_days" initialValue={3}>
                    <InputNumber min={1} max={30} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Гарантия</Text>} name="is_warranty" valuePropName="checked" initialValue={false}>
                    <Checkbox>Да</Checkbox>
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="has_delivery" valuePropName="checked" initialValue={false}>
                <Checkbox>Доставка</Checkbox>
              </Form.Item>
            </Card>
          </Col>

          <Col span={8}>
            <Card size="small" title="👥 Персонал" style={{ background: bg, border: `1px solid ${borderColor}`, overflow: "visible" }} styles={{ body: { overflow: "visible", padding: "16px" } }}>
              <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Менеджер</Text>} name="manager_id">
                <Select options={users.filter((u: any) => u.role_name === 'manager').map((u: any) => ({ label: u.full_name || u.username, value: u.id }))} allowClear placeholder="—" />
              </Form.Item>
              <Form.Item label={<Text style={{ color: labelColor, fontSize: 12 }}>Мастер</Text>} name="master_id">
                <Select options={users.filter((u: any) => u.role_name === 'master').map((u: any) => ({ label: u.full_name || u.username, value: u.id }))} allowClear placeholder="—" />
              </Form.Item>
            </Card>
          </Col>

          <Col span={8}>
            <Card size="small" title="🖨️ Печать" style={{ background: bg, border: `1px solid ${borderColor}`, overflow: "visible" }} styles={{ body: { overflow: "visible", padding: "16px" } }}>
              <Checkbox.Group value={documentsToPrint} onChange={(vals: string[]) => setDocumentsToPrint(vals as string[])} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <Checkbox value="receipt">📄 Квитанция</Checkbox>
                <Checkbox value="diagnostic">🔍 Акт диагностики</Checkbox>
                <Checkbox value="work_act">📋 Акт выполненных работ</Checkbox>
                <Checkbox value="invoice">💰 Счёт</Checkbox>
              </Checkbox.Group>
            </Card>
          </Col>
        </Row>
      </Form>
    </div>
  )
}

export default OrderCreatePage
