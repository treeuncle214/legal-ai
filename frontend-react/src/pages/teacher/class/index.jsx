import { useState } from 'react';
import { Button, message } from 'antd';
import { PlusOutlined, UploadOutlined } from '@ant-design/icons';
import { useClassManagement } from './hooks/useClassManagement';
import { ClassList } from './components/ClassList';
import { CreateClassModal } from './components/CreateClassModal';
import { ImportStudentsModal } from './components/ImportStudentsModal';
import { ClassTeacherModal } from './components/ClassTeacherModal';

export default function ClassManagement() {
    const {
        classes,
        allTeachers,
        loading,
        isAdmin,
        handleCreateClass,
        handleDeleteClass,
        handleBatchImport,
    } = useClassManagement();

    const [createClassOpen, setCreateClassOpen] = useState(false);
    const [importOpen, setImportOpen] = useState(false);
    const [teacherModalOpen, setTeacherModalOpen] = useState(false);
    const [selectedClass, setSelectedClass] = useState(null);
    const [createLoading, setCreateLoading] = useState(false);
    const [importLoading, setImportLoading] = useState(false);

    const handleCreateClassWrapper = async (name, teacherUsername) => {
        setCreateLoading(true);
        try {
            await handleCreateClass(name, teacherUsername);
            setCreateClassOpen(false);
        } finally {
            setCreateLoading(false);
        }
    };

    const handleImportWrapper = async (formData) => {
        setImportLoading(true);
        try {
            const result = await handleBatchImport(formData);
            return result;
        } finally {
            setImportLoading(false);
        }
    };

    const handleManageTeachers = (classInfo) => {
        setSelectedClass(classInfo);
        setTeacherModalOpen(true);
    };

    return (
        <>
            <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateClassOpen(true)}>
                    创建班级
                </Button>
                <Button icon={<UploadOutlined />} onClick={() => setImportOpen(true)}>
                    批量导入学生
                </Button>
            </div>

            <ClassList
                data={classes}
                loading={loading}
                onDelete={handleDeleteClass}
                onManageTeachers={handleManageTeachers}
            />

            <CreateClassModal
                open={createClassOpen}
                onCancel={() => setCreateClassOpen(false)}
                onOk={handleCreateClassWrapper}
                loading={createLoading}
                isAdmin={isAdmin}
                teachers={allTeachers}
            />

            <ImportStudentsModal
                open={importOpen}
                onCancel={() => setImportOpen(false)}
                onImport={handleImportWrapper}
                loading={importLoading}
                classes={classes}
                isAdmin={isAdmin}
            />

            <ClassTeacherModal
                open={teacherModalOpen}
                classInfo={selectedClass}
                onCancel={() => setTeacherModalOpen(false)}
                onSuccess={() => {
                    // 刷新班级列表
                    window.location.reload();
                }}
            />
        </>
    );
}