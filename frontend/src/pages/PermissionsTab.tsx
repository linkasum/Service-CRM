import React, { useEffect, useState } from 'react'
import {
  Card, Checkbox, Button, Table, Select, Space, message, Popconfirm,
  Row, Col, Typography, Divider, Tag,
} from 'antd'
import { PlusOutlined, DeleteOutlined, SaveOutlined, UserOutlined } from '@ant-design/icons'
import {
  getRoles, getUsers,
} from '../api'
import api from '../api'

const { Text, Title } = Typography

interface Section {
  label: string
  actions: Record<string, string>
}

interface RoleRow {
  role_name: string
  role_id: number
  matrix: Record<string, Record<string, boolean>>
}

const PermissionsTab: React.FC = () => {
  const [rolesData, setRolesData] = useState<RoleRow[]>([])
  const [sections, setSections] = useState<Record<string, Section>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [individualPerms, setIndividualPerms] = useState<any[]>([])
  const [users, setUsers] = useState<any[]>([])
  const [addPermUserId, setAddPermUserId] = useState<number | null>(null)
  const [addPermValue, setAddPermValue] = useState('')

  useEffect(() => { loadAll() }, [])

  const loadAll = async () => {
    setLoading(true)
    try {
      const res = await api.get('/permissions/roles-summary')
      setRolesData(res.data.roles)
      setSections(res.data.sections)
      await loadIndividual()
      await loadUsers()
    } catch (e: any) {
      message.error(`Ошибка загрузки: ${e.response?.data?.detail || e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const loadIndividual = async () => {
    try {
      const res = await api.get('/permissions/individual')
      setIndividualPerms(res.data)
    } catch {}
  }

  const loadUsers = async () => {
    try {
      const data = await getUsers()
      setUsers(data.items || data)
    } catch {}
  }

  const togglePerm = (roleName: string, action: string) => {
    setRolesData(prev =>
      prev.map(r => {
        if (r.role_name !== roleName) return r
        const section = action.split(':')[0]
        return {
          ...r,
          matrix: {
            ...r.matrix,
            [section]: {
              ...r.matrix[section],
              [action]: !r.matrix[section]?.[action],
            },
          },
        }
      }),
    )
  }

  const handleSaveAll = async () => {
    setSaving(true)
    const rolesPayload: Record<string, string[]> = {}
    for (const role of rolesData) {
      const perms: string[] = []
      for (const [section, actions] of Object.entries(role.matrix)) {
        for (const [action, enabled] of Object.entries(actions)) {
          if (enabled) perms.push(action)
        }
      }
      rolesPayload[role.role_name] = perms
    }
    try {
      await api.put('/permissions/roles-batch', { roles: rolesPayload })
      message.success('Права сохранены')
      await loadAll()
    } catch (e: any) {
      message.error(`Ошибка сохранения: ${e.response?.data?.detail || e.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleAddIndividual = async () => {
    if (!addPermUserId || !addPermValue) return
    try {
      await api.post('/permissions/individual', { user_id: addPermUserId, permission: addPermValue })
      message.success('Добавлено')
      setAddPermUserId(null)
      setAddPermValue('')
      loadIndividual()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const handleRemoveIndividual = async (id: number) => {
    try {
      await api.delete(`/permissions/individual/${id}`)
      message.success('Удалено')
      loadIndividual()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const sectionKeys = Object.keys(sections)

  return (
    <div>
      <Title level={4}>Права доступа</Title>

      {loading ? <Text>Загрузка...</Text> : (
        <>
          <Card title="Права ролей" size="small" style={{ marginBottom: 16 }}
                extra={
                  <Button type="primary" icon={<SaveOutlined />}
                          onClick={handleSaveAll} loading={saving}>
                    Сохранить все
                  </Button>
                }>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                <thead>
                  <tr>
                    <th style={{ padding: '8px 12px', textAlign: 'left', borderBottom: '2px solid #e8e8e8', minWidth: 100 }}>
                      Роль
                    </th>
                    {sectionKeys.map(sk => (
                      <th key={sk} style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '2px solid #e8e8e8' }}>
                        <div style={{ fontWeight: 600, marginBottom: 2 }}>
                          {sections[sk]?.label || sk}
                        </div>
                      </th>
                    ))}
                  </tr>
                  <tr style={{ background: '#fafafa' }}>
                    <th style={{ padding: '4px 12px' }}></th>
                    {sectionKeys.map(sk => (
                      <th key={sk} style={{ padding: '4px 8px', textAlign: 'center' }}>
                        {Object.entries(sections[sk]?.actions || {}).map(([aKey, aLabel]) => (
                          <div key={aKey} style={{ fontSize: 11, color: '#888', whiteSpace: 'nowrap' }}>
                            {aLabel}
                          </div>
                        ))}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rolesData.map(role => (
                    <tr key={role.role_name} style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <td style={{ padding: '8px 12px', fontWeight: 500 }}>
                        <Tag color="blue">{role.role_name}</Tag>
                      </td>
                      {sectionKeys.map(sk => {
                        const actions = Object.keys(sections[sk]?.actions || {})
                        return (
                          <td key={sk} style={{ padding: '4px 8px', textAlign: 'center', verticalAlign: 'middle' }}>
                            {actions.map(action => (
                              <Checkbox
                                key={action}
                                checked={role.matrix[sk]?.[action] ?? false}
                                onChange={() => togglePerm(role.role_name, action)}
                                style={{ marginRight: 6 }}
                              />
                            ))}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Divider />

          <Card title="Индивидуальные разрешения" size="small">
            <Space style={{ marginBottom: 12 }} wrap>
              <Select
                placeholder="Сотрудник"
                showSearch
                filterOption={(input, option) =>
                  (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
                }
                options={users.map(u => ({ label: u.username, value: u.id }))}
                value={addPermUserId}
                onChange={(v) => setAddPermUserId(v)}
                style={{ width: 200 }}
              />
              <Select
                placeholder="Разрешение"
                value={addPermValue || undefined}
                onChange={(v) => setAddPermValue(v)}
                style={{ width: 220 }}
              >
                {Object.entries(sections).map(([section, info]) =>
                  Object.entries(info.actions).map(([action, label]) => (
                    <Select.Option key={action} value={action}>{info.label}: {label}</Select.Option>
                  ))
                )}
                <Select.Option value="-orders:delete">ЗАПРЕТ: Удаление заказа</Select.Option>
                <Select.Option value="-orders:issue">ЗАПРЕТ: Статус "Выдан"</Select.Option>
              </Select>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAddIndividual}
                      disabled={!addPermUserId || !addPermValue}>
                Добавить
              </Button>
            </Space>

            {individualPerms.length === 0 ? (
              <Text type="secondary">Нет индивидуальных разрешений</Text>
            ) : (
              <Space wrap>
                {individualPerms.map((ip: any) => (
                  <Popconfirm key={ip.id} title="Удалить?" onConfirm={() => handleRemoveIndividual(ip.id)}>
                    <Tag closable color={ip.permission.startsWith('-') ? 'red' : 'green'} onClose={(e) => { e.preventDefault() }}>
                      <UserOutlined /> {ip.username}: {ip.permission}
                    </Tag>
                  </Popconfirm>
                ))}
              </Space>
            )}
          </Card>
        </>
      )}
    </div>
  )
}

export default PermissionsTab
