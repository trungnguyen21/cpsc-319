import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";

type Prop = { children: ReactNode}

const ProtectedRoute = ({ children }: Prop) => {
    const isAuthenticated = localStorage.getItem('token')

    if (!isAuthenticated) {
        return <Navigate to='/' replace />
    }
    return children;
};

export default ProtectedRoute;